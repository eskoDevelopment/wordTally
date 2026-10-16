# wordTally

wordTally is a feature-rich, high-performance Python Discord bot built with discord.py that allows server administrators and users to create custom phrase counters. It offers dynamic alias mapping, multi-word condition matching, and configurable real-time notifications.

## Features

* Multi-Word & Alias Matching: Match complex phrases using logical groupings. Use comma (,) as an AND operator across word groups and pipe (|) as an OR operator for word aliases.

* Case-Insensitive & Automatic Substring Matching: Smart token parsing catches root word variations automatically without redundant alias definitions.

* Flexible Real-Time Notifications: Enable instant channel responses on word triggers or run tallies silently in the background.

* Server Startup Broadcasting: Automatic on_ready broadcast checks notify designated system or text channels when the bot becomes online.

* Slash Commands: Complete integration with Discord's app_commands (CommandTree) interface.

Add to your server here!
[https://discord.com/oauth2/authorize?client_id=1560355344428040404&permissions=2147552256&integration_type=0&scope=bot+applications.commands
](https://discord.com/oauth2/authorize?client_id=1560355344428040404&permissions=277025459200&integration_type=0&scope=bot+applications.commands)
## Commands Summary

| Command | Description |
| ----- | ----- |
| /createtally | Create a new phrase counter with custom aliases, initial value, and notification settings. |
| /edittally | Update existing tally parameters (words, count, or notification toggles). |
| /deletetally | Remove a tally counter from the server. |
| /tally | View current stats and configuration for a specific counter. |
| /tallylist | Display all configured tally counters active in the server. |

## Syntax Guide

### Creating a Tally (/createtally)

```
/createtally name:<tally_name> words:<word_groups> initial_count:<number> instant_notify:<True|False>
```

#### Syntax Rules:

1. Commas (,): Separate distinct required word groups. All groups separated by a comma must be present in a single message to trigger the count.

2. Pipes (|): Separate alternative aliases inside a group. Any alias within the group will satisfy that condition.

#### Example:

```
/createtally name:davids words:please|pleasing,my|your|yours,david instant_notify:True
```

* Trigger condition: Must contain (please OR pleasing) AND (my OR your OR yours) AND (david).

## Installation & Setup

### Prerequisites

* Python 3.10 or higher
* Discord Developer Application & Bot Token

### Local Deployment

1. Clone the repository:

   ```
   git clone https://github.com/eskoDevelopment/wordTally.git
   cd wordTally
   ```

2. Set up a virtual environment (optional but recommended):

   ```
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:

   ```
   pip install discord.py python-dotenv
   ```

4. Configure Environment Variables:
   Create a .env file in the root directory:

   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

5. Run the bot:

   ```
   python bot.py
   ```

## License

Distributed under the MIT License. See LICENCE.txt for details.
