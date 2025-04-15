#!/usr/bin/env python
from typing import List, Dict
import sys
import os
import json
import logging
import time

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

from crews.multi_modal_analysis_crew.multi_modal_analysis_crew import MultiModalAnalysisCrew
from tools.xhs_comment_post_tool import XhsCommentPostTool
from crews.comments_writer_crew.comments_writer_crew import CommentsWriter


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("social_media_flow.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FlowState(BaseModel):
    """Flow状态管理"""
    note_id: str = ""
    note_url: str = ""
    image_analysis: Dict = {}
    comments: List[Dict] = []
    publish_results: List[Dict] = []

    inputs: Dict = {
            "note_id": "67c97579000000000900f651",
            "type": "normal",
            "title": "逐本香养 | 复方精油知多少",
            "desc": "如果说单方精油是风味各异的基酒饮料\n那复方精油就已调制完成的鸡尾酒\n性格鲜明，各有所长，新手更友好\n\t\n睡眠 | 银河六律精油\n芳菲散落人间梦，从此信步星河间\n恬静花草香，助易入睡，提升深睡\n熬夜冠军拍手觉好",
            "video_url": "",
            "time": 1741338078000,
            "last_update_time": 1742362687000,
            "user_id": "5c74a59f0000000011027e27",
            "nickname": "逐本",
            "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/65f14eed9df93e000176591e.jpg",
            "liked_count": "10+",
            "collected_count": "10+",
            "comment_count": "10+",
            "share_count": "10+",
            "ip_location": "浙江",
            "image_list": "http://sns-img-hw.xhscdn.com/spectrum/1040g34o31f6tgalsmm0g5n3kkmfkcvh705l42lg!nd_dft_wlteh_jpg_3,http://sns-img-hw.xhscdn.com/spectrum/1040g34o31emdphlhks3g5n3kkmfkcvh7jh95jk8!nd_dft_wlteh_jpg_3,http://sns-img-hw.xhscdn.com/spectrum/1040g34o31emdphlhks4g5n3kkmfkcvh75gd3r4o!nd_dft_wlteh_jpg_3,http://sns-img-hw.xhscdn.com/spectrum/1040g34o31emdphlhks405n3kkmfkcvh7j7tqu3g!nd_dft_wlteh_jpg_3,http://sns-img-hw.xhscdn.com/spectrum/1040g34o31emdphlhks505n3kkmfkcvh7s3qfefg!nd_dft_wlteh_jpg_3,http://sns-img-hw.xhscdn.com/spectrum/1040g0k031enir9005u005n3kkmfkcvh7uvimsv8!nd_dft_wlteh_jpg_3",
            "tag_list": "逐本,卸下纷扰逐本就好,逐本清欢节,直播预告,精油",
            "last_modify_ts": 1743514944391,
            "note_url": "https://www.xiaohongshu.com/explore/67c97579000000000900f651?xsec_token=ABtI3IXFiX7W0Lhc8K6MTdDa8Qt95-6T3gzGV0WgrR_lA=&xsec_source=pc_search",
            "source_keyword": "",
            "xsec_token": "ABtI3IXFiX7W0Lhc8K6MTdDa8Qt95-6T3gzGV0WgrR_lA=",
            'comment_list': [
            {
                "comment_id": "67d2ab8c000000001703a54a",
                "create_time": 1741859724000,
                "ip_location": "安徽",
                "note_id": "67c97579000000000900f651",
                "content": "到月底 我没看到这个活动",
                "user_id": "64ceea03000000000b009463",
                "nickname": "闪闪碎片",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31c0am1mngk005p6et81ip533qolbalo?imageView2/2/w/120/format/jpg",
                "sub_comment_count": 0,
                "pictures": "",
                "parent_comment_id": "67d2a658000000000f032b7c",
                "last_modify_ts": 1743675767634,
                "like_count": "0"
            },
            {
                "comment_id": "67d2ac7a0000000015000bc1",
                "create_time": 1741859962000,
                "ip_location": "浙江",
                "note_id": "67c97579000000000900f651",
                "content": "325哇",
                "user_id": "664574db00000000030309e4",
                "nickname": "三秒心动",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo312rgv8u0k06g5pi5ejdgu2f4o7nud7o?imageView2/2/w/120/format/jpg",
                "sub_comment_count": 0,
                "pictures": "",
                "parent_comment_id": "67d2ab8c000000001703a54a",
                "last_modify_ts": 1743675767727,
                "like_count": "0"
            },
            {
                "comment_id": "67d2b11a0000000018006b74",
                "create_time": 1741861146000,
                "ip_location": "安徽",
                "note_id": "67c97579000000000900f651",
                "content": "我知道 就是因为看到 所以才说现在买什么也没有",
                "user_id": "64ceea03000000000b009463",
                "nickname": "闪闪碎片",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31c0am1mngk005p6et81ip533qolbalo?imageView2/2/w/120/format/jpg",
                "sub_comment_count": 0,
                "pictures": "",
                "parent_comment_id": "67d2ac7a0000000015000bc1",
                "last_modify_ts": 1743675767807,
                "like_count": "0"
            },
            {
                "comment_id": "67d3875e00000000120171ca",
                "create_time": 1741915999000,
                "ip_location": "浙江",
                "note_id": "67c97579000000000900f651",
                "content": "哦哦哈哈哈哈[捂脸R]买早了",
                "user_id": "664574db00000000030309e4",
                "nickname": "三秒心动",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo312rgv8u0k06g5pi5ejdgu2f4o7nud7o?imageView2/2/w/120/format/jpg",
                "sub_comment_count": 0,
                "pictures": "",
                "parent_comment_id": "67d2b11a0000000018006b74",
                "last_modify_ts": 1743675767891,
                "like_count": "0"
            },
            {
                "comment_id": "67d00f710000000015017529",
                "create_time": 1741688689000,
                "ip_location": "浙江",
                "note_id": "67c97579000000000900f651",
                "content": "菲姐说过，香屏净化",
                "user_id": "664574db00000000030309e4",
                "nickname": "三秒心动",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo312rgv8u0k06g5pi5ejdgu2f4o7nud7o?imageView2/2/w/120/format/jpg",
                "sub_comment_count": 0,
                "pictures": "",
                "parent_comment_id": "67cd1e91000000000f03bff8",
                "last_modify_ts": 1743675770568,
                "like_count": "0"
            },
            {
                "comment_id": "67cd158a000000001802951b",
                "create_time": 1741493642000,
                "ip_location": "湖南",
                "note_id": "67c97579000000000900f651",
                "content": "感觉银河六律的成分都能稀释上脸了",
                "user_id": "57cd8b586a6a69694267ddaf",
                "nickname": "momo",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo30qmssuu3gq0048m3fc5lhndf8rt84o8?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "0",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675789590,
                "like_count": "0"
            },
            {
                "comment_id": "67cab6a100000000150162c7",
                "create_time": 1741338274000,
                "ip_location": "上海",
                "note_id": "67c97579000000000900f651",
                "content": "清单整理好啦 太期待啦[超喜欢R][超喜欢R][超喜欢R]",
                "user_id": "5a90fc64e8ac2b1f2c4f65a4",
                "nickname": "酒酿",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31fn2gvsenk5g4a1no7u68pd4bcp2gdg?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "0",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675789687,
                "like_count": "0"
            },
            {
                "comment_id": "67cc8e620000000017033dd2",
                "create_time": 1741459042000,
                "ip_location": "四川",
                "note_id": "67c97579000000000900f651",
                "content": "请问精油贴纸是一单一个，还是跟精油数量一致？",
                "user_id": "5790e1db50c4b420d97808de",
                "nickname": "木火少女图鉴",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/619a1c96a4bec0820a2847e4.jpg?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "2",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675713238,
                "like_count": "0"
            },
            {
                "comment_id": "67cad7e600000000180090d2",
                "create_time": 1741346791000,
                "ip_location": "新疆",
                "note_id": "67c97579000000000900f651",
                "content": "购买头皮按摩精油套组可以赠送精油手册吗[害羞R]",
                "user_id": "5c4423190000000005009ebb",
                "nickname": "是海带呀",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo30rqajj3kii5g5n244cch97lrok5jmo8?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "2",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675713328,
                "like_count": "0"
            },
            {
                "comment_id": "67d12b240000000017030691",
                "create_time": 1741761316000,
                "ip_location": "安徽",
                "note_id": "67c97579000000000900f651",
                "content": "刚买了三瓶[哭惹R][哭惹R]没有送任何",
                "user_id": "64ceea03000000000b009463",
                "nickname": "闪闪碎片",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31c0am1mngk005p6et81ip533qolbalo?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "5",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675713408,
                "like_count": "0"
            },
            {
                "comment_id": "67e3d4be0000000012001ed4",
                "create_time": 1742984382000,
                "ip_location": "陕西",
                "note_id": "67c97579000000000900f651",
                "content": "银河六律可以用来按摩吗",
                "user_id": "563d5dfd484fb64850fe8147",
                "nickname": "一只岚娃子",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/be4e54a984a21be925a215a08fb36c8b.jpg?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "1",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675713490,
                "like_count": "0"
            },
            {
                "comment_id": "67d2b21b000000001702bd15",
                "create_time": 1741861403000,
                "ip_location": "新疆",
                "note_id": "67c97579000000000900f651",
                "content": "这是香薰机能用的精油还是身体精油[哭惹R]",
                "user_id": "5a059166b1da14067aadbf61",
                "nickname": "0999.",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo30vp4atgplodg49vcca8mdfr1avhilq0?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "1",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675713572,
                "like_count": "0"
            },
            {
                "comment_id": "67d0f1b20000000018014eaa",
                "create_time": 1741746611000,
                "ip_location": "广东",
                "note_id": "67c97579000000000900f651",
                "content": "精油有什么功效？",
                "user_id": "559a8ac762a60c129514d763",
                "nickname": "min yi",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/5f5dba9d1280f700017b4fe6.jpg?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "1",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675713656,
                "like_count": "0"
            },
            {
                "comment_id": "67cb69d70000000017032017",
                "create_time": 1741384152000,
                "ip_location": "北京",
                "note_id": "67c97579000000000900f651",
                "content": "保卫或者守护油可以单买吗",
                "user_id": "6120d8c4000000000100a72c",
                "nickname": "不知道叫啥",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/166ad12ae9a7f6fbb4bbbf88d417895f.jpg?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "1",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675713742,
                "like_count": "0"
            },
            {
                "comment_id": "67cb027c0000000012017ea3",
                "create_time": 1741357692000,
                "ip_location": "天津",
                "note_id": "67c97579000000000900f651",
                "content": "是买任意精油都送全套小卡吗",
                "user_id": "5a2a93a9e8ac2b04ba1be988",
                "nickname": "Wpy.",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1000g2jo2nrbt37ok80104a05mt9qjqc878lhr3g?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "1",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675713824,
                "like_count": "0"
            },
            {
                "comment_id": "67cabf1f0000000018011213",
                "create_time": 1741340447000,
                "ip_location": "甘肃",
                "note_id": "67c97579000000000900f651",
                "content": "唇膏啥时候上",
                "user_id": "5acc494711be106dfcb5b059",
                "nickname": "Beroende",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1040g2jo31firqt2mg6004a4dqu4kfc2p9agc79g?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "1",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675713904,
                "like_count": "0"
            },
            {
                "comment_id": "67cd1e91000000000f03bff8",
                "create_time": 1741495954000,
                "ip_location": "浙江",
                "note_id": "67c97579000000000900f651",
                "content": "可以推荐下鼻炎用什么精油吗",
                "user_id": "5dee5d910000000001005339",
                "nickname": "雩风一旬",
                "is_author": "false",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/1000g2jo2l3hv2tgja0005nfebm8g8kpp1qb4moo?imageView2/2/w/120/format/jpg",
                "sub_comment_count": "1",
                "pictures": "",
                "parent_comment_id": 0,
                "last_modify_ts": 1743675713982,
                "like_count": "0"
            },
            ]
        }





class SocialMediaFlow(Flow[FlowState]):
    initial_state = FlowState

    '''
    @start()
    def analyze_note(self):
        print("Kickoff the social media flow")

        output = (
            MultiModalAnalysisCrew()
            .crew()
            .kickoff(inputs=self.state.inputs)
        )

                # 保存分析结果到state
        self.state.image_analysis = output
        self.state.note_id = self.state.inputs["note_id"]
        self.state.note_url = self.state.inputs["note_url"]

        logger.info(f"Image analysis result note_id: {self.state.note_id}")
        logger.info(f"Image analysis result note_url: {self.state.note_url}")

       return output
    '''

    #@listen(analyze_note)
    @start()
    def generate_replies(self):
        """第一步：生成评论回复"""
        logger.info("开始生成评论回复...")

        try:
            # 从 auto_reply_report.json 文件读取评论
            report_path = "auto_reply_report.json"
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    self.state.comments = report_data
                    logger.info(f"成功从 {report_path} 加载评论")
            else:
                logger.error(f"报告文件未找到: {report_path}")
                self.state.comments = []

            logger.info(f"最终评论结果: {self.state.comments}")
            return self.state.comments

        except Exception as e:
            logger.error(f"生成评论回复时出错: {e}")
            self.state.comments = []
            return []

    @listen(generate_replies)
    async def publish_comments(self):
        """第二步：发布评论"""
        logger.info("开始发布评论...")
        # test
        self.state.note_id = '67c97579000000000900f651'

        tool = None
        try:
            # 初始化评论发布工具
            tool = XhsCommentPostTool()
            results = []

            # 逐个发布评论
            for comment in self.state.comments:
                logger.info(f"发布评论: {comment}")
                try:
                    result = await tool.post_comment(
                        note_id=self.state.note_id,
                        content=comment["reply"],
                        target_comment_id=comment.get("target_comment_id")
                    )
                    results.append({
                        "content": comment["reply"],
                        "status": "success" if result["success"] else "failed",
                        "message": result.get("message", "")
                    })
                    logger.info(f"评论发布结果: {result}")
                except Exception as e:
                    logger.error(f"发布单条评论失败: {e}")
                    results.append({
                        "content": comment["reply"],
                        "status": "failed",
                        "message": str(e)
                    })
                # 更真实像人操作
                time.sleep(1)

            # 保存发布结果到state
            self.state.publish_results = results

            return {
                "success": any(r["status"] == "success" for r in results),
                "results": results
            }

        except Exception as e:
            logger.error(f"发布评论任务失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # 确保资源被清理
            if tool and tool._initialized:
                await tool.cleanup()

def kickoff():
    """启动流程"""
    try:
        flow = SocialMediaFlow()
        flow.kickoff()
    except Exception as e:
        logger.error(f"流程执行失败: {e}")
        raise

def plot():
    poem_flow = SocialMediaFlow()
    poem_flow.plot()


if __name__ == "__main__":
    kickoff()
