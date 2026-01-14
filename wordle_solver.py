#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
import argparse
import re
from pathlib import Path
from collections import Counter
from typing import Optional, List, Dict, Tuple


NORMALIZED_RUSSIAN = set("абвгдеежзийклмнопрстуфхцчшщъыьэюя")

DEFAULT_DICT = Path("~/.local/share/wordle/russian_five_letter_words.txt").expanduser()

# регулярка для проверки ровно 5 букв (после нормализации ё->е)
CYRILLIC_5_RE = re.compile(r"^[а-я]{5}$", re.IGNORECASE)


def normalize_word(word: str) -> str:
    """Нормализация слова: strip, lower, ё->е, удалить дефисы/пробелы."""
    return word.strip().lower().replace("ё", "е").replace("-", "").replace(" ", "")


def read_text_file(path: Path) -> List[str]:
    """
        Прочитать текстовый файл в кодировке UTF-8.
        Если файл не читается напрямую, пробуем прочитать с заменой некорректных символов.
    """
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()


def is_valid_five_letter_word(word: str) -> bool:
    """Проверка: ровно 5 кириллических букв после нормализации."""
    if not word:
        return False
    normalized_word = normalize_word(word)
    if not CYRILLIC_5_RE.match(normalized_word):
        return False
    # дополнительная проверка на набор букв
    return all(ch in NORMALIZED_RUSSIAN for ch in normalized_word)


def get_nouns(path: Optional[Path | str] = None) -> List[str]:
    """Вернуть список уникальных отсортированных 5-буквенных слов из файла."""
    if path is None:
        path = DEFAULT_DICT

    path = Path(path).expanduser()

    if not path.exists():
        return []

    try:
        lines = read_text_file(path)
    except Exception as e:
        print(f"Ошибка чтения файла '{path}': {e}", file=sys.stderr)
        return []

    words = set()
    for line in lines:
        w = normalize_word(line)
        if is_valid_five_letter_word(w):
            words.add(w)

    return sorted(words)


def write_words_atomic(path: Path, words: List[str]) -> None:
    """Перезаписать файл через временный файл."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for w in words:
            f.write(w + "\n")
    tmp.replace(path)


def add_word_to_dict(word: str, path: Optional[Path | str] = None) -> bool:
    if path is None:
        path = DEFAULT_DICT

    path = Path(path).expanduser() 

    w = normalize_word(word)
    if not is_valid_five_letter_word(w):
        print(f"Слово '{word}' не подходит (нужно ровно 5 кириллических букв).", file=sys.stderr)
        return False

    words = get_nouns(path)
    if w in words:
        print(f"Слово '{w}' уже есть в словаре.")
        return True

    words.append(w)
    words = sorted(set(words))

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_words_atomic(path, words)
        print(f"Слово '{w}' добавлено в '{path}'. Количество слов: {len(words)}")
        return True
    except Exception as e:
        print(f"Ошибка при записи файла '{path}': {e}", file=sys.stderr)
        return False


def remove_word_from_dict(word: str, path: Optional[Path | str] = None) -> bool:
    if path is None:
        path = DEFAULT_DICT

    path = Path(path).expanduser() 

    w = normalize_word(word)
    words = get_nouns(path)

    if w not in words:
        print(f"Слово '{w}' не найдено в словаре.")
        return False

    try:
        words.remove(w)
        write_words_atomic(path, words)
        print(f"Слово '{w}' удалено из '{path}'. Количество слов: {len(words)}")
        return True
    except Exception as e:
        print(f"Ошибка при обновлении '{path}': {e}", file=sys.stderr)
        return False


def list_words(path: Optional[Path] = None, limit: Optional[int] = None) -> None:
    words = get_nouns(path)

    if limit is not None and limit >= 0:
        words = words[:limit]

    if not words:
        print("Слова не найдены.")
        return

    for w in words:
        print(w)


def get_feedback_interactive(guess: str) -> str:
    print(f"\nПопытка: {guess.upper()}")
    while True:
        fb = input("Введите результат (0-серая, 1-желтая, 2-зеленая, пример 01020): ").strip()
        if len(fb) != 5 or any(ch not in "012" for ch in fb):
            print("Неверный формат. Введите 5 символов из {0,1,2}. Попробуйте снова.")
            continue
        return fb


def solve_wordle(wordlist_path: Optional[Path | str] = None, first_guess: str = "опера") -> None:
    wordlist_path = Path(wordlist_path).expanduser() if wordlist_path else DEFAULT_DICT

    all_words = get_nouns(wordlist_path)

    if not all_words:
        print("Словарь пуст или не найден. Завершаю.", file=sys.stderr)
        return

    possible_words = all_words.copy()
    first_guess = normalize_word(first_guess)

    for attempt in range(1, 7):
        if len(possible_words) == 0:
            print("Ошибка: нет возможных слов после фильтрации.")
            return

        if len(possible_words) == 1:
            print(f"\nУгадал! Это слово: {possible_words[0].upper()}")
            return

        if attempt == 1:
            current_guess = first_guess if first_guess in all_words else possible_words[0]
        else:
            current_guess = get_best_guess(possible_words, all_words)

        print(f"\nПопытка {attempt}/6 — пробую: {current_guess.upper()}")
        feedback = get_feedback_interactive(current_guess)

        if feedback == "22222":
            print(f"\nУгадал! Это слово: {current_guess.upper()}")
            return

        possible_words = filter_words(possible_words, current_guess, feedback)
        print(f"Осталось возможных слов: {len(possible_words)}")

        if attempt == 6:
            if len(possible_words) >= 1:
                print("\nПоследняя попытка!")
                print("Выбранное слово:", possible_words[0].upper())
                print("Оставшиеся варианты:", ", ".join(w.upper() for w in possible_words))
            else:
                print("\nПосле последней фильтрации вариантов не осталось.")

    print("\nЗадача завершена.")


def filter_words(words: List[str], guess: str, feedback: str) -> List[str]:
    result: List[str] = []
    guess_list = list(guess)

    required_counts = {}
    for i, ch in enumerate(guess_list):
        if feedback[i] in ("1", "2"):
            required_counts[ch] = required_counts.get(ch, 0) + 1

    for word in words:
        if word == guess:
            continue

        valid = True
        for i in range(5):
            if feedback[i] == "2":
                if word[i] != guess[i]:
                    valid = False
                    break
            elif feedback[i] == "1":
                if word[i] == guess[i]:
                    valid = False
                    break

        if not valid:
            continue

        for i in range(5):
            if feedback[i] == "1":
                if guess[i] not in word:
                    valid = False
                    break

        if not valid:
            continue

        word_counts = Counter(word)
        for i in range(5):
            if feedback[i] == "0":
                letter = guess[i]
                allowed = required_counts.get(letter, 0)
                if word_counts.get(letter, 0) > allowed:
                    valid = False
                    break

        if valid:
            result.append(word)

    return result


def get_best_guess(possible_words: List[str], all_words: List[str]) -> str:
    if len(possible_words) <= 2:
        return possible_words[0]

    limit = min(50, len(possible_words))
    candidates = possible_words[:limit]

    best_word = candidates[0]
    best_score = float("inf")
    for candidate in candidates:
        score = evaluate_word(candidate, possible_words)
        if score < best_score:
            best_score = score
            best_word = candidate

    return best_word


def evaluate_word(word: str, possible_words: List[str]) -> int:
    patterns: Dict[Tuple[int, int, int, int, int], int] = {}

    for target in possible_words:
        feedback = [0] * 5
        target_letters: List[Optional[str]] = list(target)
        word_letters: List[Optional[str]] = list(word)

        for i in range(5):
            if word_letters[i] == target_letters[i]:
                feedback[i] = 2
                target_letters[i] = None
                word_letters[i] = None

        for i in range(5):
            if (
                word_letters[i] is not None
                and word_letters[i] in target_letters
            ):
                feedback[i] = 1
                idx = target_letters.index(word_letters[i])
                target_letters[idx] = None

        pattern: Tuple[int, int, int, int, int] = (
            feedback[0],
            feedback[1],
            feedback[2],
            feedback[3],
            feedback[4],
        )
        patterns[pattern] = patterns.get(pattern, 0) + 1

    return max(patterns.values()) if patterns else 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='Решатель игры "5 букв" от Т-банк.',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument(
        "--words", "-w",
        help=f"Путь к файлу словаря (по умолчанию {DEFAULT_DICT})",
        default=None
    )
    p.add_argument(
        "--first", "-f",
        help='Cлово для первой попытки (по умолчанию "опера").',
        default="опера"
    )
    p.add_argument(
        "--add-word", "-a",
        help="Добавить слово в словарь и выйти.",
        default=None
    )
    p.add_argument(
        "--remove-word", "-r",
        help="Удалить слово из словаря и выйти.",
        default=None
    )
    p.add_argument(
        "--list-words", "-l",
        action="store_true",
        help="Вывести слова из словаря."
    )
    p.add_argument(
        "--limit", "-n",
        type=int,
        default=None,
        help="При --list-words: вывести первые N слов. По умолчанию все."
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    dict_path: Path = args.words if args.words else DEFAULT_DICT

    if args.add_word:
        ok = add_word_to_dict(args.add_word, path=dict_path)
        sys.exit(0 if ok else 1)

    if args.remove_word:
        ok = remove_word_from_dict(args.remove_word, path=dict_path)
        sys.exit(0 if ok else 1)

    if args.list_words:
        list_words(path=dict_path, limit=args.limit)
        sys.exit(0)

    solve_wordle(wordlist_path=dict_path, first_guess=args.first)


if __name__ == "__main__":
    main()