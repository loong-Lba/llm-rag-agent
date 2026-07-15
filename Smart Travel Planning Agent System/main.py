from search_assistant import run_search_app


# main.py 是整个项目的命令行入口文件。
# 它本身不负责实现 LangGraph 的核心逻辑，
# 而是负责：接收用户输入、调用工作流、展示结果。
def main() -> None:
    print("LangGraph 搜索助手已启动，输入 quit 退出。")

    # 使用 while True 持续接收用户输入，形成一个简单的命令行交互循环。
    while True:
        user_input = input("\n请输入你的问题：").strip()

        # 如果用户直接回车，说明这次输入为空，跳过本轮循环。
        if not user_input:
            continue

        # 提供几个常见退出命令，方便在终端中结束程序。
        if user_input.lower() in {"quit", "exit", "q"}:
            print("已退出。")
            break

        # 调用 search_assistant.py 中封装好的运行入口。
        # 这个函数内部会创建图、初始化状态、执行节点，并返回最终状态字典。
        result = run_search_app(user_input)

        # 展示“理解后的用户需求”。
        # 这里不是用户的原始提问，而是大模型整理后的问题摘要。
        print("\n=== 用户需求理解 ===")
        print(result.get("user_query", ""))

        # 展示搜索节点生成的搜索关键词。
        # 这个字段很适合调试，因为它可以帮助你判断“查询改写”是否合理。
        print("\n=== 搜索词 ===")
        print(result.get("search_query", ""))

        # 展示最终答案。
        # 如果搜索成功，这里通常是“基于实时搜索结果”的回答；
        # 如果搜索失败，这里则会退化为“基于模型已有知识”的回答。
        print("\n=== 最终答案 ===")
        print(result.get("final_answer", ""))


# Python 脚本的标准入口写法。
# 只有直接运行 main.py 时才会执行 main()；
# 如果这个文件被别的模块 import，则不会自动启动程序。
if __name__ == "__main__":
    main()
