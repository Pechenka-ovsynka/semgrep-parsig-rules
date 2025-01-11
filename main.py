import requests
import json
import ruamel.yaml
from ruamel.yaml.scalarstring import LiteralScalarString
import os

headers = {"Authorization":"Bearer {place own token}",
"Content-Type":"application/json"}

semgrep_all_rules_url_param = "https://semgrep.dev/api/registry/rules?definition=1"



def convert_multiline_strings(data):
    """
    Благодарим chat gpt, функция нужна для корректного преобразования правил семгрепа со строкам с '|' и переносами строк  из json объекта в yml файл
    """
    if isinstance(data, dict):
        return {key: convert_multiline_strings(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_multiline_strings(item) for item in data]
    elif isinstance(data, str):
        if '\n' in data:  # Если в строке есть перенос строки, преобразуем ее в многострочную
            return LiteralScalarString(data)
        else:
            return data
    else:
        return data


def create_folders_from_string(path_string, base_dir='.'):
    """
    На основе переданной строки создаём вложенные папки и файл с расширением .yml
    "foo.bar.test" -> ./foo/bar/test.yml
    """
    parts = path_string.split('.')
    # Последовательно создаём вложенные папки
    current_path = base_dir  # Базовая директория, по умолчанию - текущая
    for part in parts[:-1]:
        current_path = os.path.join(current_path, part)
        if not os.path.exists(current_path):
            os.makedirs(current_path)
    file_name = f"{parts[-1]}.yml"
    file_path = os.path.join(current_path, file_name)
    
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            file.write('')  # Создаём пустой файл


def get_all_rules():
	"""
	Просто функция, чтобы получить огромный json со всеми правилами из registry
	"""
	rules = requests.get(semgrep_all_rules_url_param, headers=headers)
	return rules.json()


def filter_community_rules(rules):
	"""
	Функция для какой-нибудь фильтрации - абсолютно опциональная, я просто оставляю только прошные 
	"""
	clear_rules = []
	i, j = 0, 0
	for rule in rules:
		if rule["meta"]["rule"]["origin"] == "pro_rules": # откидываем, если правило не прошное 
			clear_rules.append(rule)
			i += 1
		else:
			j += 1
	print(f"All rules: {len(rules)}, remove: {j}, result count: {i}")
	return clear_rules


def get_definition_rules(rules):
	"""
	Кривое вытаскивание самих правил и складывание в словарь вида {"cpp.lang.security.id_1":{rule},"python.lang.security.id_2":{rule}...}
	"""
	json_rules = {}
	for rule in rules:
		try:
			rule_path = rule["path"]
			json_rules[rule_path] = rule["definition"]
			for raw_rule in json_rules[rule_path]["rules"]:
				raw_rule["message"] = "( Parsing with script by https://t.me/hatn9g) " + raw_rule["message"] # Маленькая пасхалка и пример с обработкой самого правила, если есть желание менять\добавлять
		except Exception as err:
			print("error", err)
	print(f"prepare definition of {len(json_rules)}")
	return json_rules


def dump_rules(json_rules):
	"""
	Функция проходи по словарю, создаёт директории и сохраняет правила в yml файлы
	"""
	i = 0
	for rule in json_rules:
		i += 1
		create_folders_from_string(rule)
		yaml = ruamel.yaml.YAML(pure=True)
		yaml.indent(mapping=4, sequence=4, offset=2)
		yaml.dump(convert_multiline_strings(json_rules[rule]), open(rule.replace('.','/')+".yml","w",encoding='utf-8'))
		print("dump", rule, i)
	print("all rules dumps")


rules = get_all_rules()
rules = filter_community_rules(rules)
json_rules = get_definition_rules(rules)
dump_rules(json_rules)