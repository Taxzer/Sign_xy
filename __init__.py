import requests
import os
import execjs
import json
import time
import execjs._runner_sources as _runner_sources
import datetime


class Sign_xy:
    def __init__(self):
        # urllib3.disable_warnings()
        self.type = None
        self.webdriver = None
        self.times = None
        self.authorization = ""
        # self.sys = None
        self.node_path = None
        self.headers = {
            "schoolcertify":"10497", # 学校对应代码
            "Host":"ccnu.ai-augmented.com",
            "Content-Type":"application/json; charset=utf-8",
            "access-control-allow-methods":"GET,POST,OPTIONS",
            "Accept-Encoding":"gzip, deflate, br",
            "Connection":"keep-alive",
            "If-None-Match":"W/47-Gkgd+hPnYQ+HOAd1+Mgij152K58",
            "Accept":"*/*",
            "User-Agent":"xiaoya_mobile",
            "Authorization":self.authorization,
            "Accept-Language":"en-US,en;q=0.9",
            "Access-Control-Allow-Origin":"*",
        }
        self.url = "https://{}".format(self.headers["Host"])
        self.sessions = requests.Session()
        self.account = {
            "username": "",
            "password": ""
        }

    def login(self):
        if os.path.exists(os.path.split(os.path.realpath(__file__))[0] + "/authorization.txt"):
            print("Cookies exists. Try to login by using cookies.")
            with open(os.path.split(os.path.realpath(__file__))[0] + "/authorization.txt", "r") as f:
                self.headers["Authorization"] = "Bearer " + f.readline().strip("\n")
            self.sessions.headers.update(self.headers)
            # self.sessions.get("{}/api")
            # self.getUserInfo()
            result = json.loads(self.getUserInfo().text)
            if result["code"] != 200:
                print("Cookies has expired. Sign in automatically.")
                os.remove("./authorization.txt")
                return False

        else:
            print("Try to login by username and password")
            local_node_runtime = execjs.ExternalRuntime(
                name="Node.js (V8) local",
                command='',
                encoding='UTF-8',
                runner_source=_runner_sources.Node
            )
            local_node_runtime._binary_cache = [os.path.split(os.path.realpath(__file__))[0] + self.node_path]
            local_node_runtime._available = True
            execjs.register('local_node', local_node_runtime)
            with open(os.path.split(os.path.realpath(__file__))[0] + "/Algorithm.js", encoding="UTF-8") as f:
                # cxk = node.compile(f.read())
                cxk = execjs.get('local_node').compile(f.read())
            funName = "crack"
            password = cxk.call(funName, self.account["password"])
            # self.headers.pop("Authorization")
            result = self.sessions.post("https://{}/api/jw-starcmooc/user/unifiedCheckLogin".format(self.headers["Host"]), verify=False, json={
                "password":password,
                "loginName":self.account["username"]
            }, headers=self.headers)
            token = json.loads(result.text)["result"]["token"]
            with open(os.path.split(os.path.realpath(__file__))[0] + "/authorization.txt", "w") as f:
                f.write(token)
            self.headers["Authorization"] = "Bearer {}".format(token)
            self.sessions.headers.update(self.headers)
            # print(1)
        userinfo = json.loads(self.getUserInfo().text)
        realname = userinfo["result"]["realname"]
        signInfo = userinfo["result"]["sign"]  # 可能是签到信息，暂且留空
        print("Login successfully. Welcome, {}".format(realname))
        return True
        # for i in group_id["data"]:
            # print(i["id"]) 所有课程id
        # print(1)

    def getUserInfo(self):
        return self.sessions.get("https://{}/api/jw-starcmooc/user/currentUserInfo".format(self.headers["Host"]),verify=False)

    def sign(self):
        if not self.times:
            self.times = 1
        else:
            self.times = int(self.times)
        for times in range(self.times):
            for i in self.getGroup_id():  # 暂且写为所有课程都签到一遍
                # self.getRegister_id(i)
                result = self.getRegister_id(i.strip("\n"))
                if result["data"]["signing_register"] != []:
                    result1 = self.sessions.post("https://{}/api/jx-iresource/register/sign".format(self.headers["Host"]), json={
                        "check_type": "1",
                        "register_id": i.strip("\n")
                    }, verify=False)
                    result1 = json.loads(result1.text)
                    if result1["code"] == 0:
                        print("{}   {}签到成功".format(str(datetime.datetime.now())[0:-7], result["data"]["group_name"]))
                        return
                    elif result1["code"] == 50011:
                        print("{}   {}已经签到过了".format(str(datetime.datetime.now())[0:-7], result["data"]["group_name"]))
                        return
                    else:
                        print("{}   {}{}".format(str(datetime.datetime.now())[0:-7], result["data"]["group_name"],
                                                 result1["message"]))
                        return
            time.sleep(60)  # 不建议改动

            # else:
            #     print("此课程不需要签到")

    def getRegister_id(self, group_id):
        return json.loads(self.sessions.get(
            "https://{}/api/jx-iresource/course/getOpenCourse?group_id={}&is_in_course=2".format(self.headers["Host"],
                group_id), verify=False).text)

    def get_tasks(self, group_id):
        result = self.sessions.get("https://ccnu.ai-augmented.com/api/jx-stat/group/task/queryTaskNotices", params={
            "group_id": group_id,
            "role": 1
        })
        return json.loads(result.text)["data"]["student_tasks"]

    def finish_media(self):
        try:
            count = 0
            for j in self.getGroup_id():
                tasks = self.get_tasks(j.strip("\n"))
                for i in tasks:
                    if i["task_type"] == 1 and i["finish"] == 0:
                        result = self.sessions.get("https://ccnu.ai-augmented.com/api/jx-iresource/vod/duration/{}".format(i["quote_id"])).text
                        result = json.loads(result)
                        if not result["success"]:
                            continue
                        result = result["data"]
                        watched_duration = max(0, float(result["duration"]) - float(result["watched_duration"]) + 1)
                        self.sessions.post("https://ccnu.ai-augmented.com/api/jx-iresource/vod/duration/{}".format(i["quote_id"]), json={
                            "media_type": result["media_type"],  # 类型为录音
                            "duration": result["duration"],  # 总时间
                            "played": 1,  # 播放次数
                            "watched_duration": watched_duration  # 已经看过的时长
                        })
                        result = self.sessions.post("https://ccnu.ai-augmented.com/api/jx-iresource/vod/checkTaskStatus", json={
                            "task_id": i["task_id"],
                            "media_id": i["quote_id"],
                            "assign_id": i["assign_id"],
                            "group_id": i["group_id"]
                        })
                        count += 1
            print(f"完成了{count}个作业")
        except Exception as e:
            print(str(type(e)) + ":" + str(e))

    def getGroup_id(self):
        if os.path.exists(os.path.split(os.path.realpath(__file__))[0] + "/group_id.txt"):
            with open(os.path.split(os.path.realpath(__file__))[0] + "/group_id.txt", "r") as f:
                result = f.readlines()
        else:
            result = json.loads(self.sessions.get("https://{}/api/jx-iresource/group/student/groups?time_flag=1".format(self.headers["Host"]),verify=False).text)["data"]
            tmp = []
            for i in result:
                tmp.append(i["id"])
            with open(os.path.split(os.path.realpath(__file__))[0] + "/group_id.txt", "w") as f:
                f.write("\n".join(tmp))
            return tmp
        # if os.path.exists("./group_id.txt"):
        return result

    def run(self):
        if not self.type:
            return
        if self.account["username"] == "" or self.account["password"] == "":
            if os.path.exists(os.path.split(os.path.realpath(__file__))[0] + "/account.txt"):
                with open(os.path.split(os.path.realpath(__file__))[0] + "/account.txt", "r") as f:
                    account_list = f.readlines()
                    self.account["username"] = account_list[0].strip("\n").strip(" ")
                    self.account["password"] = account_list[1].strip("\n").strip(" ")
            else:
                print("请填入账号密码。注意：账号密码为你统一身份认证的账号密码")
                self.account["username"] = input("学号：")
                self.account["password"] = input("密码：")
                with open(os.path.split(os.path.realpath(__file__))[0] + "/account.txt", "w") as f:
                    f.write(self.account["username"] + "\n" + self.account["password"] + "\n")
        if not self.login():
            self.login()
        if self.type == "刷课":
            self.finish_media()   # 自动刷课，刷视频接口
        elif self.type == "签到":
            self.sign()
