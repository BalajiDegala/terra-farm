# 10 — Expressions, console, and the dependency graph

[Previous](09-events.md) · [Index](../README.md) · [Next](11-state.md)

**Goal:** explain the configuration you have built. **Start:** Chapter 09 passed; repository root.
This chapter adds no files/resources, but advances the copier's sequence marker.

## 1. Inspect a no-change plan

```text
python scripts/chapter.py 10
cd lab
terraform fmt -check -recursive
terraform validate
terraform plan
terraform state list
```

Expect no changes. Do not apply just to generate activity.

## 2. Practice in the console

```text
terraform console
```

Enter these expressions one at a time (then enter `exit`):

| Expression | Expected idea |
| --- | --- |
| `upper("dev")` | `"DEV"` |
| `lower(replace("MY_SHOP", "_", "-"))` | `"my-shop"` |
| `format("%s-%s", "shop", "dev")` | `"shop-dev"` |
| `merge({Environment = "test"}, {Environment = "dev"})` | Later map value wins |
| `toset(["one", "two", "two"])` | Two unique elements; no meaningful sequence |
| `lookup(local.common_tags, "Owner", "unassigned")` | Fallback unless you set Owner |
| `try(aws_sns_topic.order_failures[0].arn, null)` | ARN if enabled, otherwise null |
| `jsonencode({app = "shop", enabled = true})` | Valid JSON string |
| `var.environment == "prod" ? 30 : 7` | 7 with the default inputs |
| `local.name_prefix` | Current normalized project/environment prefix |

Find `templatefile()` in `generated.tf`: it turns resource-derived values into the generated JSON.
Functions operate on values; providers perform API operations. Variables are inputs, locals are
derived values, and outputs are the public results. All three are expressions, not cloud resources.

## 3. Read the graph

```text
terraform graph
```

Follow the path from the DLQ to orders queue to event-source mapping. References define this directed
acyclic graph (DAG); file order does not. Independent nodes can run concurrently.
If Graphviz is installed, save a picture without PowerShell's binary-redirection pitfalls:

```text
python ../scripts/graph.py
```

Open `generated/terraform-graph.png`. The helper pipes Terraform's DOT bytes to `dot -Tpng -o ...`.
Graphviz is optional; the DOT text is enough for the exercise.

## 4. Inspect iteration and lifecycle

`for_each` keeps addresses stable by name (`["create_order"]`, `["environment"]`). `count` uses
integer indexes (`[0]`); removing an item from a longer indexed list can shift later addresses.
The failure topic's on/off switch is a suitable small `count` example.

The API deployment uses `create_before_destroy` for a concrete dependency need. `prevent_destroy`
would block planned deletion while that lifecycle rule remains in configuration; it is not a backup.
`ignore_changes` tells Terraform to tolerate selected drift and should only be used for deliberate
shared ownership. Neither is added here because the lab needs visible drift and reliable cleanup.
The identity data source's lifecycle postcondition checks a returned value rather than creation order.

**Checkpoint:** explain one implicit dependency, one explicit dependency, and a conditional in this project.
**Exercise:** predict the results of `lookup` and `try` before entering them; explain how they differ.
**Troubleshooting:** exit the console before another Terraform command; it can hold a state lock.
For a missing `dot`, skip the optional image or install [Graphviz](https://graphviz.org/download/).
