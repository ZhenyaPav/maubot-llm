def get_character() -> str:
    char_file = "/home/zhenyapav/Projects/maubot-llm/char.txt"
    file = open(char_file, "r")
    string = file.read()
    file.close()
    return string