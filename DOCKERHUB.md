# DockerHub Configuration

## Публикация образов на DockerHub

Проект настроен для автоматической публикации Docker образов на DockerHub через GitHub Actions.

## Настройка

### 1. Создайте аккаунт на DockerHub

1. Зарегистрируйтесь на [DockerHub](https://hub.docker.com/)
2. Создайте репозиторий для проекта (например, `parser-project`)

### 2. Настройте GitHub Secrets

В настройках репозитория GitHub добавьте следующие secrets:

- `DOCKERHUB_USERNAME` - ваш username на DockerHub
- `DOCKERHUB_TOKEN` - токен доступа (можно создать в DockerHub → Account Settings → Security)

### 3. Workflow автоматически запустится

При каждом push в ветку `master` или `main`, а также при создании тега `v*`, образы будут автоматически собираться и публиковаться.

## Использование образов

После публикации образы будут доступны по адресам:

```bash
# Web сервис
docker pull <your-username>/parser-project-web:latest

# Или конкретная версия
docker pull <your-username>/parser-project-web:v1.0.0
```

## Локальная сборка

Для локальной сборки используйте:

```bash
docker build -t parser-project-web ./web
```

## Теги

- `latest` - последняя версия из master/main
- `v1.0.0` - версии по семантическому версионированию
- `sha-<commit>` - по SHA коммита

## Обновление docker-compose.yml

После публикации на DockerHub можно обновить `docker-compose.yml`:

```yaml
web:
  image: <your-username>/parser-project-web:latest
  # вместо build: context: ./web
```

