import argparse

import PySimpleGUI as sg

from benchmarker import init_parser, process_args


def create_gui(parser: argparse.ArgumentParser) -> None:
    layout = []
    input_elements = {}

    for action in parser._actions[1:]:
        # Check if action has options, i.e. can accept a value
        if action.option_strings:
            checkbox_name = f"checkbox__{action.dest}"
            input_name = f"input__{action.dest}"
            long_option_name = action.option_strings[-1][2:]
            if action.nargs == 0:
                layout.append(
                    [
                        sg.Checkbox(
                            long_option_name,
                            key=checkbox_name,
                            enable_events=True,
                            default=action.default,
                            tooltip=action.help,
                        )
                    ]
                )
            else:
                layout.append(
                    [
                        sg.Checkbox(
                            long_option_name,
                            key=checkbox_name,
                            enable_events=True,
                            tooltip=action.help,
                        )
                    ]
                )
                field = sg.Input(
                    default_text=action.default, size=(20, 1), key=input_name, tooltip=action.help
                )
                layout[-1].append(field)
            input_elements[checkbox_name] = input_name

    layout.append([sg.Button("Run Benchmark"), sg.Button("Cancel")])
    window = sg.Window("Factorio Headless Server Manager", layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Cancel"):
            break
        if event == "Run Benchmark":
            args = []
            for checkbox, input_field in input_elements.items():
                if values[checkbox]:
                    action = parser._option_string_actions[f"--{checkbox.split('__')[1]}"]
                    option_name = action.dest
                    args.append(f"--{option_name}")
                    if input_field in values:
                        args.append(values[input_field])
            print(args)
            process_args(init_parser().parse_args(args))

    window.close()


if __name__ == "__main__":
    parser = init_parser()
    create_gui(parser)
