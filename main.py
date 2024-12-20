import requests
import os
import argparse
import xml.etree.ElementTree as ET
import zipfile
import subprocess

def download_file(url, save_path):
    if os.path.exists(save_path):
        print(f"Файл {save_path} уже существует. Пропуск скачивания.")
        return save_path  # Возвращаем путь, если файл существует

    try:
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            print(f"Ошибка при скачивании: {response.status_code}. Ответ: {response.text[:200]}...")  # Логируем начало ответа
            return None
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):  # Chunking for efficient download
                file.write(chunk)
        print(f"Файл успешно скачан и сохранен в: {save_path}")

        # Проверка на валидность ZIP файла
        if not zipfile.is_zipfile(save_path):
            print(f"Ошибка: файл {save_path} не является архивом ZIP.")
            with open(save_path, 'r', encoding='utf-8') as f:
                print(f"Содержимое файла {save_path}:")
                print(f.read())  # Логируем содержимое файла, если это текстовый файл
            return None  # Возвращаем None, чтобы дальнейшая обработка не продолжалась
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except requests.exceptions.RequestException as err:
        print(f"Ошибка при запросе: {err}")  # More specific exception handling
    except Exception as err:
        print(f"Произошла ошибка: {err}")

    return save_path


def get_dependencies(package_name, package_version, depth=0, max_depth=1, all_dependencies=None):
    if all_dependencies is None:
        all_dependencies = {}

    if depth > max_depth:
        return all_dependencies

    url = f"https://www.nuget.org/api/v2/package/{package_name}/{package_version}"  # URL для получения пакета
    save_directory = r"C:/Users/Anastasia/PycharmProjects/konfig2"
    save_file_path = os.path.join(save_directory, f"{package_name}.{package_version}.nupkg")

    # Скачиваем файл
    downloaded_file_path = download_file(url, save_file_path)
    if downloaded_file_path is None:  # Если файл не валиден
        return all_dependencies

    nupkg_path = downloaded_file_path

    try:
        with zipfile.ZipFile(nupkg_path, 'r') as zip_ref:
            nuspec_file = [f for f in zip_ref.namelist() if f.endswith('.nuspec')]
            if nuspec_file:
                with zip_ref.open(nuspec_file[0]) as file:
                    tree = ET.parse(file)
                    root = tree.getroot()
                    namespaces = {'ns': 'http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd'}

                    dependencies_set = set()
                    authors_set = set()

                    # Получаем зависимости
                    for dependency in root.findall(".//ns:dependency", namespaces):
                        dep_id = dependency.get('id')
                        dep_version = dependency.get('version')
                        if dep_id and dep_version:
                            dep_package = f"{dep_id}.{dep_version}"  # Форматирование зависимости
                            dependencies_set.add(dep_package)
                            if dep_package not in all_dependencies:
                                all_dependencies[dep_package] = {'dependencies': set(), 'authors': set()}
                                get_dependencies(dep_id, dep_version, depth + 1, max_depth, all_dependencies)

                    # Получаем авторов
                    authors = root.find(".//ns:authors", namespaces)
                    if authors is not None and authors.text:
                        authors_set.update(authors.text.split(','))

                    # Сохраняем зависимости и авторов в словаре
                    all_dependencies[f"{package_name}.{package_version}"] = {
                        'dependencies': dependencies_set,
                        'authors': authors_set
                    }

    except Exception as e:
        print(f"Ошибка при обработке {package_name}.{package_version}: {e}")

    return all_dependencies

def print_authors(all_dependencies):
    for package, info in all_dependencies.items():
        authors = info.get('authors', set())
        if authors:
            print(f"Пакет: {package}")
            print("Авторы:", ", ".join(authors))
        else:
            print(f"Пакет: {package} не имеет информации об авторах.")


def generate_puml_graph(all_dependencies, puml_path):
    with open(puml_path, 'w') as file:
        file.write("@startuml\n")

        # Для отладки выводим зависимости
        print(f"Dependencies data: {all_dependencies}")

        for package, details in all_dependencies.items():
            package_name, package_version = package.rsplit('.', 1)  # Разделяем имя пакета и его версию
            authors = details.get('authors', set())
            authors_str = ", ".join(authors) if authors else "unknown"

            # Создаем блок для пакета с версией
            file.write(f'package "{package_name} {package_version}" as {package_name} {{\n')

            # Добавляем информацию о версии и авторах как примечание внутри пакета
            file.write(f'    note right of {package_name} : Version: {package_version}\n')
            file.write(f'    note right of {package_name} : Authors: {authors_str}\n')

            # Добавляем связи с зависимостями (только имена зависимостей)
            for dep in details.get('dependencies', set()):
                dep_name, dep_version = dep.rsplit('.', 1)  # Разделяем имя зависимости и ее версию
                file.write(f'    {package_name} --> {dep_name}\n')  # Связь с зависимостью (без версий)

            file.write('}\n')

        file.write("@enduml\n")


def generate_png_from_puml(puml_path, output_png_path, plantuml_path):
    try:
        subprocess.run(['java', '-jar', plantuml_path, puml_path, '-o', os.path.dirname(output_png_path)], check=True)
        print(f"PNG график сохранен в {output_png_path}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при генерации PNG: {e}")

def main():
    package_name = "Newtonsoft.Json.Bson"
    package_version = "1.0.3"
    all_dependencies = get_dependencies(package_name, package_version)
    print(all_dependencies)

    # Печать авторов
    print_authors(all_dependencies)

    # Путь для сохранения PlantUML графика
    puml_path = "graph_dependencies.puml"
    output_png_path = "C://Users//Anastasia//PycharmProjects//konfig2//graph_dependencies.png"
    plantuml_path = "C://Users//Anastasia//Downloads//plantuml-1.2024.8.jar"

    # Генерация графа в формате PlantUML
    generate_puml_graph(all_dependencies, puml_path)

    # Генерация PNG из графа
    generate_png_from_puml(puml_path, output_png_path, plantuml_path)

if __name__ == "__main__":
    main()