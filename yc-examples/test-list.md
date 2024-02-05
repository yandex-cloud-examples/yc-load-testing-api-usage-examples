# Tests listing

In the snippets, it is assumed that folder-id setting is already set in `yc`

```bash
yc config set folder-id 'my_folder_id'
```

## 1. All tests in folder

```bash
yc loadtesting test list
```

## 2. All tests with name containing 'api-examples'

```bash
yc loadtesting test list --filter "details.name CONTAINS 'api-examples'"
```

## 3. All tests with tags 'issue:123' and 'type:release'

```bash
yc loadtesting test list --filter "details.tags.issue:123 and details.tags.type:release"
```

## 4. All tests created by account with id 'loadtester'

```bash
yc loadtesting test list --filter "summary.created_by = 'loadtester'"
```

## 5. All tests created at 29 Jan 2024

```bash
yc loadtesting test list --filter "summary.created_at >= 2024-01-29 AND summary.created_at < 2024-01-30"
```

## 6. All tests in 2023 which are not finished yet

```bash
yc loadtesting test list --filter "summary.is_finished = false AND summary.created_at >= 2023-01-01 AND summary.created_at < 2024-01-01"
```
