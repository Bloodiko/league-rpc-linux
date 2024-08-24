import argparse
import sys
import threading

import asyncio

import nest_asyncio  # type:ignore


from league_rpc.lcu_api.lcu_connector import start_connector

from league_rpc.processes.process import (
    check_discord_process,
    check_league_client_process,
)

from league_rpc.utils.color import Color
from league_rpc.utils.const import DEFAULT_CLIENT_ID, DEFAULT_LEAGUE_CLIENT_EXE_PATH, DISCORD_PROCESS_NAMES


def main(cli_args: argparse.Namespace) -> None:
    """
    This is the program that gets executed.
    """
    ############################################################
    ## Check Discord, RiotClient & LeagueClient processes     ##
    check_league_client_process(cli_args)

    rpc = check_discord_process(
        process_names=DISCORD_PROCESS_NAMES + cli_args.add_process,
        client_id=cli_args.client_id,
        wait_for_discord=cli_args.wait_for_discord,
    )

    # Start LCU_Thread
    # This process will connect to the LCU API and updates the rpc based on data subscribed from the LCU API.
    # In this case passing the rpc object to the process is easier than trying to return updated data from the process.
    # Every In-Client update will be handled by the LCU_Thread process and will update the rpc accordingly.
    lcu_process = threading.Thread(
        target=start_connector,
        args=(
            rpc,
            cli_args,
        ),
        daemon=True,
    )
    lcu_process.start()

    print(f"\n{Color.green}Successfully connected to Discord RPC!{Color.reset}")

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print(f"{Color.red}Shutting down the program..{Color.reset}")
        rpc.close()
        sys.exit()

    ############################################################


if __name__ == "__main__":
    # Patch for asyncio - read more here: https://pypi.org/project/nest-asyncio/
    nest_asyncio.apply()  # type: ignore

    parser = argparse.ArgumentParser(description="Script with Discord RPC.")
    parser.add_argument(
        "--client-id",
        type=str,
        default=DEFAULT_CLIENT_ID,
        help=f"Client ID for Discord RPC. Default is {DEFAULT_CLIENT_ID}. which will show 'League of Legends' on Discord",
    )
    parser.add_argument(
        "--no-stats",
        action="store_true",
        help="use '--no-stats' to Opt out of showing in-game stats (KDA, minions) in Discord RPC",
    )
    parser.add_argument(
        "--show-emojis",
        "--emojis",
        action="store_true",
        help="use '--show-emojis' to show green/red circle emoji, depending on your Online status in league.",
    )
    parser.add_argument(
        "--no-rank",
        action="store_true",
        help="use '--no-rank' to hide your SoloQ/Flex/Tft/Arena Rank in Discord RPC",
    )
    parser.add_argument(
        "--add-process",
        nargs="+",
        default=[],
        help="Add custom Discord process names to the search list.",
    )
    parser.add_argument(
        "--wait-for-league",
        type=int,
        default=-1,
        help="Time in seconds to wait for the League client to start. -1 for infinite waiting, Good when used as a starting script for league.",
    )
    parser.add_argument(
        "--wait-for-discord",
        type=int,
        default=-1,
        help="Time in seconds to wait for the Discord client to start. -1 for infinite waiting, Good when you want to start this script before you've had time to start Discord.",
    )
    parser.add_argument(
        "--launch-league",
        type=str,
        default=DEFAULT_LEAGUE_CLIENT_EXE_PATH,
        help=f"Path to the League of Legends client executable. Default path is: {DEFAULT_LEAGUE_CLIENT_EXE_PATH}",
    )

    args: argparse.Namespace = parser.parse_args()

    # Prints the League RPC logo
    print(Color().logo)

    if args.no_stats:
        print(
            f"{Color.green}Argument {Color.blue}--no-stats{Color.green} detected.. Will {Color.red}not {Color.green}show InGame stats{Color.reset}"
        )
    if args.no_rank:
        print(
            f"{Color.green}Argument {Color.blue}--no-rank{Color.green} detected.. Will hide your league rank.{Color.reset}"
        )
    if args.show_emojis:
        print(
            f"{Color.green}Argument {Color.blue}--show-emojis, --emojis{Color.green} detected.. Will show emojis. such as league status indicators on Discord.{Color.reset}"
        )
    if args.add_process:
        print(
            f"{Color.green}Argument {Color.blue}--add-process{Color.green} detected.. Will add {Color.blue}{args.add_process}{Color.green} to the list of Discord processes to look for.{Color.reset}"
        )

    if args.client_id != DEFAULT_CLIENT_ID:
        print(
            f"{Color.green}Argument {Color.blue}--client-id{Color.green} detected.. Will try to connect by using {Color.blue}({args.client_id}){Color.reset}"
        )
    if args.wait_for_league and args.wait_for_league > 0:
        print(
            f"{Color.green}Argument {Color.blue}--wait-for-league{Color.green} detected.. {Color.blue}will wait for League to start before continuing{Color.reset}"
        )
    if args.wait_for_discord and args.wait_for_discord > 0:
        print(
            f"{Color.green}Argument {Color.blue}--wait-for-discord{Color.green} detected.. {Color.blue}will wait for Discord to start before continuing{Color.reset}"
        )

    if args.launch_league:
        if args.launch_league == DEFAULT_LEAGUE_CLIENT_EXE_PATH:
            print(
                f"{Color.green}Attempting to launch the League client at the default location{Color.reset} {Color.blue}{args.launch_league}{Color.reset}\n"
                f"{Color.green}If league is already running, it will not launch a new instance.{Color.reset}\n"
                f"{Color.orange}If the League client does not launch, please specify the path manually using: --launch-league <path>{Color.reset}\n"
            )
        else:
            print(
                f"{Color.green}Detected the {Color.blue}--launch-league{Color.green} argument with a custom path. Attempting to launch the League client, from: {Color.blue}{args.launch_league}{Color.reset}\n"
                f"{Color.orange}If league is already running, it will not launch a new instance.{Color.reset}\n"
            )

    main(cli_args=args)
