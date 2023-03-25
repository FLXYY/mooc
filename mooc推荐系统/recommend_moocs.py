# -*-coding:utf-8-*-
import os

os.environ["DJANGO_SETTINGS_MODULE"] = "mooc.settings"
import django

django.setup()
from user.models import *
from math import sqrt, pow
import operator
from django.db.models import Subquery, Q, Count


# from django.shortcuts import render,render_to_response
class UserCf:

    # 获得初始化数据
    def __init__(self, all_user):
        self.all_user = all_user

    # 通过用户名获得商品列表，仅调试使用
    def getItems(self, username1, username2):
        return self.all_user[username1], self.all_user[username2]

    # 计算两个用户的皮尔逊相关系数
    def pearson(self, user1, user2):  # 数据格式为：商品id，浏览此
        sum_xy = 0.0  # user1,user2 每项打分的成绩的累加
        n = 0  # 公共浏览次数
        sum_x = 0.0  # user1 的打分总和
        sum_y = 0.0  # user2 的打分总和
        sumX2 = 0.0  # user1每项打分平方的累加
        sumY2 = 0.0  # user2每项打分平方的累加
        for mooc1, score1 in user1.items():
            if mooc1 in user2.keys():  # 计算公共的浏览次数
                n += 1
                sum_xy += score1 * user2[mooc1]
                sum_x += score1
                sum_y += user2[mooc1]
                sumX2 += pow(score1, 2)
                sumY2 += pow(user2[mooc1], 2)
        if n == 0:
            # print("p氏距离为0")
            return 0
        molecule = sum_xy - (sum_x * sum_y) / n  # 分子
        denominator = sqrt((sumX2 - pow(sum_x, 2) / n) * (sumY2 - pow(sum_y, 2) / n))  # 分母
        if denominator == 0:
            return 0
        r = molecule / denominator
        return r

    # 计算与当前用户的距离，获得最临近的用户
    def nearest_user(self, current_user, n=1):
        distances = {}
        # 用户，相似度
        # 遍历整个数据集
        for user, rate_set in self.all_user.items():
            # 非当前的用户
            if user != current_user:
                distance = self.pearson(self.all_user[current_user], self.all_user[user])
                # 计算两个用户的相似度
                distances[user] = distance
        closest_distance = sorted(
            distances.items(), key=operator.itemgetter(1), reverse=True
        )
        # 最相似的N个用户
        # print("closest user:", closest_distance[:n])
        return closest_distance[:n]

    # 给用户推荐商品
    def recommend(self, username, n=1):
        recommend = {}
        nearest_user = self.nearest_user(username, n)
        for user, score in dict(nearest_user).items():  # 最相近的n个用户
            for moocs, scores in self.all_user[user].items():  # 推荐的用户的商品列表
                if moocs not in self.all_user[username].keys():  # 当前username没有看过
                    if moocs not in recommend.keys():  # 添加到推荐列表中
                        recommend[moocs] = scores * score
        # 对推荐的结果按照商品浏览次数排序
        return sorted(recommend.items(), key=operator.itemgetter(1), reverse=True)


# 入口函数
def recommend_by_user_id(user_id):
    current_user = User.objects.get(id=user_id)
    # 如果当前用户没有打分 则按照热度顺序返回
    if current_user.rate_set.count() == 0:
        mooc_list = Mooc.objects.all().order_by("-sump")[:15]
        return mooc_list
    users = User.objects.all()
    all_user = {}
    for user in users:
        rates = user.rate_set.all()
        rate = {}
        # 用户有给课程打分 在rate和all_user中进行设置
        if rates:
            for i in rates:
                rate.setdefault(str(i.mooc.id), i.mark)
            all_user.setdefault(user.username, rate)
        else:
            # 用户没有为课程打过分，设为0
            all_user.setdefault(user.username, {})

    user_cf = UserCf(all_user=all_user)
    recommend_list = user_cf.recommend(current_user.username, 15)
    good_list = [each[0] for each in recommend_list]
    mooc_list = list(Mooc.objects.filter(id__in=good_list).order_by("-sump")[:15])
    other_length = 15 - len(mooc_list)
    if other_length > 0:
        fix_list = Mooc.objects.filter(~Q(rate__user_id=user_id)).order_by('-sump')[:other_length]
        mooc_list.extend(list(fix_list))
        for fix in fix_list:
            if fix not in mooc_list:
                mooc_list.append(fix)
            if len(mooc_list) >= 15:
                break
    return mooc_list


# 计算相似度
def similarity(mooc1_id, mooc2_id):
    mooc1_set = Rate.objects.filter(mooc_id=mooc1_id)
    # mooc1的打分用户数
    mooc1_sum = mooc1_set.count()
    # mooc_2的打分用户数
    mooc2_sum = Rate.objects.filter(mooc_id=mooc2_id).count()
    # 两者的交集
    common = Rate.objects.filter(user_id__in=Subquery(mooc1_set.values('user_id')), mooc=mooc2_id).values('user_id').count()
    # 没有人给当前课程打分
    if mooc1_sum == 0 or mooc2_sum == 0:
        return 0
    similar_value = common / sqrt(mooc1_sum * mooc2_sum)
    return similar_value


#
def recommend_by_item_id(user_id, k=15):
    # 未看过的课程
    # 前三的tag
    most_tags = Tags.objects.annotate(tags_sum=Count('name')).order_by('-tags_sum').filter(mooc__rate__user_id=user_id).order_by('-tags_sum')[:3]
    un_watched = Mooc.objects.filter(~Q(rate__user_id=user_id), tags__in=most_tags)[:15]
    # 看过的课程
    watched = Rate.objects.filter(user_id=user_id).values_list('mooc_id', 'mark')
    # print(un_watched.query)
    distances = []
    # 在未看过的课程中找到
    # 后续改进，选择top15
    for un_watched_mooc in un_watched:
        for watched_mooc in watched:
            distances.append((similarity(un_watched_mooc.id, watched_mooc[0]) * watched_mooc[1], un_watched_mooc))
    distances.sort(key=lambda x: x[0], reverse=True)
    recommend_list = []
    for mark, mooc in distances:
        if len(recommend_list) >= k:
            break
        if mooc not in recommend_list:
            recommend_list.append(mooc)
    # print('this is recommend list', recommend_list)
    # 如果得不到有效数量的推荐 按照未看过的课程中的热度进行填充
    return recommend_list


if __name__ == '__main__':
    similarity(2003, 2008)
    recommend_by_item_id(1)
