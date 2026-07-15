from ..mymcp.MCPServer import build_medical_vector_store


if __name__ == "__main__":
    result = build_medical_vector_store()
    print(f"构建成功，共写入 {result['count']} 条医疗文档到 {result['persist_directory']}")
