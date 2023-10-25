import re
def replace_tags(source:str, char_name:str, user_name:str) -> str:
    rep = {
        '{{char}}':char_name,
        '{{user}}':user_name,
        '<START>':"***"
    }
    rep = dict((re.escape(k),v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))
    result = pattern.sub(lambda m: rep[re.escape(m.group(0))], source)
    return result