from investment_pipeline.config import load_env_file


def test_load_env_file_reads_simple_key_values(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        """
# comment
OPENAI_API_KEY='sk-test'
OPENAI_MODEL=gpt-test
""".strip(),
        encoding="utf-8",
    )

    values = load_env_file(env_path)

    assert values["OPENAI_API_KEY"] == "sk-test"
    assert values["OPENAI_MODEL"] == "gpt-test"
