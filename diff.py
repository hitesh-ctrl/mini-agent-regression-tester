import json 

scenario_ids = ["scenario_01", "scenario_02", "scenario_03","scenario_04"]

for sid in scenario_ids:
    with open(f"{sid}.json", "r") as f:
        baseline = json.load(f)


    with open(f"replay_{sid}.json", "r") as f:
        replay = json.load(f)

    b_tool = baseline["tool_called"]
    r_tool = replay["tool_called"]

    if b_tool != r_tool:
        if b_tool == "issue_refund" and r_tool is None:
            
            if baseline["result"]["success"]:
                print(f"{sid}: REGRESSION - replay stopped calling the tool where baseline issued a VALID refund")
            else:
                print(f"{sid}: VALID CHANGE - baseline's tool call failed anyway ({baseline['result']['reason']}); replay correctly avoided attempting it")
            continue

        elif b_tool is None and r_tool == "issue_refund":
            # baseline didn't call it, replay did.
            if replay["result"]["success"]:
                print(f"{sid}: REGRESSION - replay started calling the tool where baseline correctly did not")
            else:
                print(f"{sid}: VALID CHANGE - replay attempted a call baseline didn't, but it failed safely ({replay['result']['reason']})")

        else:


            print(f"{sid}: DIFFERENT - unexpected combination, review manually")
    
    elif b_tool is None:
        print(f"{sid}: SAME - neither version called the tool")
    else:
        if baseline["arguments"] == replay["arguments"]:
            print(f"{sid}: SAME - identical arguments: {baseline['arguments']}")
        else:
            print(f"{sid}: DIFFERENT - baseline args {baseline['arguments']}, replay args {replay['arguments']}")
