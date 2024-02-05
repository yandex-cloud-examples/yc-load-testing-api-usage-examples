# Test lifetime

In the snippets, it is assumed that folder-id setting is already set in `yc`:

```bash
yc config set folder-id 'my_folder_id'
```

## Delete test

```bash
yc loadtesting test delete "my_test_id"
```

### Delete all tests in CREATED status

```bash
export TESTS_TO_DELETE=$(yc loadtesting test list --filter "summary.status = CREATED and summary.created_by = $AUTHOR" --format json | jq -r "[.[].id] | join(\" \")")
echo $TESTS_TO_DELETE | xargs yc loadtesting test delete
```

## Stop running test

```bash
yc loadtesting test stop "my_test_id"
```

### Stop all running tests

```bash
export TESTS_TO_STOP=$(yc loadtesting test list --filter "summary.status not in (CREATED, DONE, STOPPED, AUTOSTOPPED, FAILED)" --format json | jq -r "[.[].id] | join(\" \")")
echo $TESTS_TO_STOP | xargs yc loadtesting test stop
```
