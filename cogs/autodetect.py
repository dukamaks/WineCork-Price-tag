import os
import re
import asyncio
def sep(string):
    number_pattern = r'\d+'
    unit_pattern = r'[^\d\s]+'
    numbers = re.findall(number_pattern, string)
    if len(numbers) == 2:
        try:
            num  = ".".join(numbers)
            test = str(float(num))
            test_test = test.replace(".", ",")
        except:
            pass
    elif len(numbers) == 1:
        test_test = numbers[0]
    units = re.findall(unit_pattern, string)
    if units[0] == "мл": 
        test_test = str(float(int(test_test)/1000))
        test_test = test_test.replace(".", ",")
        units[0] = "л"
    return f"{test_test} {str(units[0] if len(units) == 1 else units[1]).lower()}"


def w_detect(third_name):
    quantity_pattern = r"\d+(?:[,\.]\d+)?\s*(?:г|кг|мл|л|гр|шт|штук|штуки)"
    quantity_match = re.search(quantity_pattern, third_name, re.IGNORECASE)
    weight = None
    if quantity_match:
        quantity = quantity_match.group()
        weight = sep(quantity)
    third_name_clean = re.sub(quantity_pattern, "", third_name, flags=re.IGNORECASE).strip()
    for word in banwords:
        third_name_clean = re.sub(r'\b{}\b'.format(re.escape(word)), "", third_name_clean, flags=re.IGNORECASE)
    result = re.sub(r'(?<!\d)[,.](?!\d)', '', third_name_clean).replace("(", "").replace(")", "").strip()
    
    return result, weight if weight else "None"

banwords = [
"ШОТЛАНДІЯ",
"АВСТРАЛІЯ",
"АВСТРІЯ",
"АРГЕНТИНА",
"БАРБАДОС",
"ВЕЛИКА БРИТАНІЯ",
"ГРЕЦІЯ",
"ГРУЗІЯ",
"ІРЛАНДІЯ",
"ІСПАНІЯ",
"ІТАЛІЯ",
"КАНАДА",
"МЕКСИКА",
"МОЛДОВА",
"НІДЕРЛАНДИ",
"НІМЕЧЧИНА",
"НОВА ЗЕЛАНДІЯ",
"ПАНАМА",
"ПАР",
"ПОРТУГАЛІЯ",
"СЛОВАЧЧИНА",
"СЛОВЕНІЯ",
"США",
"ТАЙВАНЬ",
"УКРАЇНА",
"УРУГВАЙ",
"ФРАНЦІЯ",
"ЧІЛІ",
"ВИНОГРАДНЕ"
]
if __name__ == "__main__":
    print(w_detect("Штопор Pullparrot Chrome, Pulltex (Іспанія)"))
    print(w_detect("Пиво темне фільтр. пастер. Айінгер Селебратор 330мл"))
