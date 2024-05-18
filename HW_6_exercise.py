import sys
from pathlib import Path
from collections import UserDict
import re
from datetime import datetime, timedelta
import pickle


# Валідація вводу та обробка помилок


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return "Не достатньо аргументів. Будь ласка, дотримуйтесь формату команди."
        except ValueError:
            return "Некоректні дані. Переконайтеся, що ви вводите правильні типи даних."
        except KeyError:
            return "Контакт не знайдено."
    return inner


# Базовий клас для полів запису


class Field:
    def __init__(self, value):
        self.value = value  # Ініціалізація значення поля

    def __str__(self):
        return str(self.value)  # Повертає строкове представлення поля


# Клас для зберігання імені контакту


class Name(Field):
    pass  # Наслідування базових властивостей класу Field


# Клас для зберігання номера телефону з валідацією


class Phone(Field):
    def __init__(self, value):
        if not re.fullmatch(r"\d{10}", value):
            raise ValueError("Номер телефону повинен містити рівно 10 цифр.")
        super().__init__(value)  # Виклик конструктора базового класу


# Клас для зберігання дати народження з валідацією


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, '%d.%m.%Y').date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


# Клас для зберігання інформації про контакт


class Record:
    def __init__(self, name):
        self.name = Name(name)  # Збереження імені як об'єкту класу Name
        self.phones = []  # Ініціалізація списку телефонів
        self.birthday = None  # Ініціалізація дня народження

    def add_phone(self, phone):
        self.phones.append(Phone(phone))  # Додавання нового телефону

    def remove_phone(self, phone_number):
        # Видалення телефону
        self.phones = [
            phone for phone in self.phones if phone.value != phone_number]

    def edit_phone(self, old_number, new_number):
        found = False
        for phone in self.phones:
            if phone.value == old_number:
                phone.value = new_number  # Оновлення номеру телефону
                found = True
                break
        if not found:
            raise ValueError("Номер телефону не знайдено.")

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone  # Пошук телефону за номером
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)  # Додавання дня народження

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        birthday = self.birthday.value.strftime(
            '%d.%m.%Y') if self.birthday else "No birthday"
        return f"Name: {self.name.value}, Phones: {phones}, Birthday: {birthday}"


# Клас для зберігання та управління записами


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record  # Додавання запису

    def find(self, name):
        return self.data.get(name, None)  # Пошук запису за ім'ям

    def delete(self, name):
        if name in self.data:
            del self.data[name]  # Видалення запису
        else:
            raise KeyError("Запис не знайдено.")

    def get_upcoming_birthdays(self, days=7):
        today = datetime.today().date()
        upcoming_birthdays = []
        for record in self.data.values():
            if record.birthday:
                birthday = record.birthday.value.replace(year=today.year)
                if today <= birthday <= today + timedelta(days=days):
                    upcoming_birthdays.append(record)
        return upcoming_birthdays


# Серіалізація з pickle


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено


# Функції для обробки команд CLI


def parse_input(user_input):
    cmd, *args = user_input.split()  # Розбір введення на команду та аргументи
    cmd = cmd.strip().lower()  # Нормалізація команди
    return cmd, args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book):
    if len(args) != 3:
        raise IndexError("Введіть ім'я, старий телефон і новий телефон.")
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Телефон для {name} оновлено з {old_phone} на {new_phone}."
    else:
        raise KeyError(f"Контакт '{name}' не знайдено.")


@input_error
def show_phone(args, book):
    if len(args) != 1:
        raise IndexError("Введіть точно одне ім'я.")
    name = args[0]
    record = book.find(name)
    if record:
        return f"{name}: {'; '.join(phone.value for phone in record.phones)}"
    else:
        raise KeyError(f"Контакт '{name}' не знайдено.")


@input_error
def show_all(book):
    if not book.data:
        return "Контакти відсутні."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book):
    if len(args) != 2:
        raise IndexError(
            "Please provide a name and a birthday in the format DD.MM.YYYY.")
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f"Birthday for {name} added as {birthday}."
    else:
        raise KeyError(f"Contact '{name}' not found.")


@input_error
def show_birthday(args, book):
    if len(args) != 1:
        raise IndexError("Please provide a name.")
    name = args[0]
    record = book.find(name)
    if record:
        if record.birthday:
            return f"{name}'s birthday is on {record.birthday.value.strftime('%d.%m.%Y')}."
        else:
            return f"{name} does not have a birthday set."
    else:
        raise KeyError(f"Contact '{name}' not found.")


@input_error
def birthdays(args, book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No birthdays in the next week."
    return "\n".join(str(record) for record in upcoming_birthdays)


def main():
    book = load_data()  # Завантажити дані з файлу при запуску програми
    print("Welcome to the assistant bot!")  # Вітальне повідомлення

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)  # Зберегти дані перед виходом з програми
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()


# Список команд, які вміє виконувати цей бот(код):

# 1. hello  - відповідає привітанням і запитує, чим може допомогти. # Виводить: "How can I help you?"


# 2. add < name > <phone > -  додає новий контакт з ім'ям <name> і номером телефону <phone> або оновлює існуючий контакт.
# Виводить: "Contact added." або "Contact updated."


# 3. change <name> <old_phone> <new_phone> - змінює номер телефону для існуючого контакту з іменем <name>.
# Виводить: "Телефон для <name> оновлено з <old_phone> на <new_phone>."


# 4. phone <name> - показує номери телефонів для заданого контакту з ім'ям <name>.
# Виводить: "<name>: <список телефонів>"


# 5. all - показує всі контакти в адресній книзі.
# Виводить: список контактів


# 6. add-birthday <name> <birthday>  - додає або оновлює день народження для контакту з ім'ям <name>.
# Виводить: "Birthday for <name> added as <birthday>."


# 7. show-birthday <name> - показує день народження для заданого контакту з ім'ям <name>.
# Виводить: "<name>'s birthday is on <дата>." або "<name> does not have a birthday set."


# 8. birthdays - показує контакти, у яких день народження наступає протягом найближчого тижня.
# Виводить: список контактів з днями народження


# 9. close або exit - завершує роботу бота і зберігає дані адресної книги у файл.
# Виводить: "Good bye!"
