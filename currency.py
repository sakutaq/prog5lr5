import time
from collections import namedtuple
from xml.etree import ElementTree as ET
import requests
import matplotlib.pyplot as plt

# Реализация чисел с плавающей точкой
FloatNumber = namedtuple('FloatNumber', ['integer', 'fractional'])

# Шаблон "Одиночка" с использованием метакласса
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class CentralBankRates(metaclass=SingletonMeta):
    def __init__(self, request_interval=1):
        self.request_interval = request_interval
        self._last_request_time = 0

    def _wait_for_next_request(self):
        elapsed_time = time.time() - self._last_request_time
        if elapsed_time < self.request_interval:
            time.sleep(self.request_interval - elapsed_time)
        self._last_request_time = time.time()

    def get_currencies(self, currency_codes=None):
        """
        Получает курсы валют с сайта ЦБ РФ и возвращает их в формате списка.
        """
        self._wait_for_next_request()

        try:
            response = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Ошибка при запросе данных: {e}")
            return []

        root = ET.fromstring(response.content)
        valutes = root.findall("Valute")

        result = []
        for _v in valutes:
            valute_id = _v.get('ID')
            valute = {}
            if currency_codes is None or valute_id in currency_codes:
                name = _v.find('Name').text
                value = _v.find('Value').text.replace(',', '.')
                nominal = int(_v.find('Nominal').text)
                char_code = _v.find('CharCode').text

                # Сохраняем в формате FloatNumber
                integer, fractional = value.split('.')
                float_number = FloatNumber(integer, fractional)

                # Если номинал не равен 1, учитываем его
                if nominal != 1:
                    adjusted_value = FloatNumber(
                        str(round(float(value) / nominal, 2)).split('.')[0],
                        str(round(float(value) / nominal, 2)).split('.')[1]
                    )
                    valute[char_code] = (name, adjusted_value)
                else:
                    valute[char_code] = (name, float_number)

                result.append(valute)

        return result


class CurrenciesLst:
    def __init__(self, currencies):
        self.currencies = currencies

    def __len__(self):
        return len(self.currencies)

    def __iter__(self):
        return iter(self.currencies)

    def visualize_currencies(self, filename="currencies.jpg"):
        """
        Визуализация курсов валют в виде графика.
        """
        names = []
        values = []
        for item in self.currencies:
            for code, (name, value) in item.items():
                names.append(name)
                values.append(float(value.integer + '.' + value.fractional))

        plt.figure(figsize=(10, 6))
        plt.bar(names, values)
        plt.xlabel("Валюта")
        plt.ylabel("Курс (RUB)")
        plt.title("Курсы валют ЦБ РФ")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(filename)
        plt.show()


# Тестирование
import unittest


class TestCentralBankRates(unittest.TestCase):
    def setUp(self):
        self.cbr = CentralBankRates(request_interval=1)

    def test_invalid_currency_code(self):
        result = self.cbr.get_currencies(['R9999'])
        self.assertEqual(result, [])

    def test_valid_currency_code(self):
        result = self.cbr.get_currencies(['R01035'])
        self.assertTrue(len(result) > 0)
        for item in result:
            for code, (name, value) in item.items():
                self.assertTrue(isinstance(name, str))
                self.assertTrue(isinstance(value, FloatNumber))
                self.assertTrue(0 <= int(value.integer) <= 999)

    def test_visualization(self):
        currencies = [{'USD': ('Доллар США', FloatNumber('75', '3214'))}]
        lst = CurrenciesLst(currencies)
        lst.visualize_currencies()


if __name__ == "__main__":
    # Использование
    cbr = CentralBankRates(request_interval=2)
    currencies = cbr.get_currencies(['R01035', 'R01335', 'R01700J'])
    currency_list = CurrenciesLst(currencies)
    currency_list.visualize_currencies()

    # Запуск тестов
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
