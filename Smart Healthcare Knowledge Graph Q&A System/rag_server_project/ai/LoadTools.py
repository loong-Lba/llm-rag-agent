# 导入MCP客户端封装的的函数
from ..mymcp import MCPClient
from typing import Dict, Any

"""
    在这里的工具定义函数中，需要通过函数描述文档来给agent说明这个工具中的信息、调用规则等[必写]
"""


# 数据库工具
def find_email(sql: str, params: str | None = None) -> Dict[str, Any]:
    """
        数据库中有一张用户表users，其结构信息如下：
            user_id: 主键自增ID
            username: 用户名
            email：邮箱号
        在通过用户名查询邮箱号信息的时候调用这个工具,这个工具只能够实现查询操作，比如：
        `select * from users where username=%s`
    """
    return MCPClient.call_mcp_tool("find_email", sql=sql, params=params or [])


# 发送邮件的工具
def send_email(receiver: str) -> Dict[str, Any]:
    """
        在发送邮件的时候调用这个工具
    """
    return MCPClient.call_mcp_tool("send_email", receiver=receiver)


# 验证验证码的工具
def verify_code(receiver: str, code: str) -> Dict[str, Any]:
    """
        在执行验证码验证的时候调用这个工具
        receiver：收件方的邮箱号，作为redis查询的key
        code: 用户输入的验证码
    """
    return MCPClient.call_mcp_tool("verify_code", receiver=receiver, code=code)


# 医疗混合检索工具
def search_medical_hybrid(question: str, top_k: int = 10, rerank_top_k: int = 3) -> Dict[str, Any]:
    """
        当用户询问疾病介绍、症状、药物、科室、检查、治疗方式、饮食、并发症、病因、预防、费用、治愈率等信息时，
        可调用这个工具执行基于 Neo4j 医疗图谱文本化语料的向量检索 + BM25 检索 + RRF 混合检索。
        question：用户问题
        top_k：向量检索与 BM25 检索各自召回的候选数量
        rerank_top_k：融合后保留的最终候选数量
    """
    return MCPClient.call_mcp_tool(
        "search_medical_hybrid",
        question=question,
        top_k=top_k,
        rerank_top_k=rerank_top_k,
    )


# Neo4j 图谱查询工具
def find_data(cypher: str, params: dict | None = None) -> Dict[str, Any]:
    """
        当用户询问医疗知识图谱中的疾病、症状、药物、科室、检查、治疗方式、食物、菜谱、并发症等信息时，调用这个工具。
        只允许生成 MATCH / RETURN 类型的 Cypher 查询，不允许生成 CREATE、MERGE、DELETE、SET。

        图谱中的节点标签：
            Disease：疾病
            Category：疾病分类
            Symptom：症状
            Department：科室
            Cureway：治疗方式
            Check：检查项目
            Drug：药物
            Food：食物
            Dishes：菜谱

        图谱中的关系类型：
            DISEASE_CATEGORY：疾病所属类别
            DISEASE_SYMPTOM：疾病症状
            DISEASE_ACOMPANY：疾病并发症或伴随疾病
            DISEASE_DEPARTMENT：就诊科室
            DISEASE_CUREWAY：治疗方式
            DISEASE_CHECK：检查项目
            DISEASE_DRUG：相关药物
            DISEASE_DO_EAT：推荐食物
            DISEASE_NOT_EAT：不推荐食物
            DISEASE_DISHES：推荐菜谱

        Disease 节点常用属性：
            name：疾病名称
            desc：疾病介绍
            prevent：预防措施
            cause：病因
            yibao_status：是否医保
            get_prob：患病概率
            get_way：传染方式
            cure_lasttime：治疗周期
            cured_prob：治愈概率
            cost_money：治疗费用
    """
    return MCPClient.call_mcp_tool("find_data", cypher=cypher, params=params or {})
