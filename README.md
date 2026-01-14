# Решатель игры "5 букв" от Т-банк

В этом репозитории представлена небольшая утилита-CLI. Скрипт позволяет находить пятибуквенные слова, загаданные в игре от Т-банк. Поиск слов осуществляется по локальному словарю. Есть возможность добавлять, удалять и просматривать слова из словаря.

## Требования для скрипта

- Python 3.8+

## Установка на Linux

1. Клонировать репозиторий.

```bash
git clone https://github.com/Sharero/tinkoff_five_letters_solver.git ~/wordle
cd ~/wordle
```

2. Установить скрипт как команду `wordle`.

```bash
sudo install -m 755 wordle_solver.py /usr/local/bin/wordle \
  && sudo mkdir -p ~/.local/share/wordle \
  && sudo install -m 644 russian_five_letter_words.txt ~/.local/share/wordle/
```
Скрипт хранится в **/usr/local/bin/wordle**.
Словарь хранится в **~/.local/share/wordle/russian_five_letter_words.txt**.

## Описание CLI опций

```scss
--words, -w    Путь к файлу словаря (по умолчанию ~/.local/share/wordle/russian_five_letter_words.txt)
--first, -f    Cлово для первой попытки (по умолчанию "опера")
--add-word, -a Добавить слово в словарь и выйти
--remove-word, -r Удалить слово из словаря и выйти
--list-words, -l Вывести слова из словаря
--limit, -n    При --list-words: вывести первые N слов (по умолчанию все)
```

## Примеры использования

- Запустить решатель
```bash
wordle
# или с явным словарём и стартовым словом
wordle --words /path/to/dict.txt --first опера
```

- Добавить слово в словарь
```bash
wordle --add-word самса
# или указать файл словаря
wordle --add-word самса --words /path/to/dict.txt
```

- Удалить слово из словаря
```bash
wordle --remove-word самса
```

- Вывести слова из словаря
```bash
wordle --list-words
# вывести первые 100 слов
wordle --list-words --limit 100
```
