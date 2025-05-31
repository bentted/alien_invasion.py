import requests

class ChatBot:
    def __init__(self, server_url, bot_username="ChatBot"):
        self.server_url = server_url
        self.bot_username = bot_username

    def send_message(self, message):
        payload = {"username": self.bot_username, "message": message}
        try:
            response = requests.post(f"{self.server_url}/api/chat", json=payload, timeout=5)
            response.raise_for_status()
            print(f"Bot message sent: {message}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending bot message: {e}")

    def handle_command(self, command):
        if command == "/help":
            self.send_message("Available commands: /help, /rules, /leaderboard")
        elif command == "/rules":
            self.send_message("Chat Rules: Be respectful. No spamming. Follow the community guidelines.")
        elif command == "/leaderboard":
            try:
                response = requests.get(f"{self.server_url}/api/leaderboard", timeout=5)
                response.raise_for_status()
                leaderboard = response.json()
                leaderboard_message = "Leaderboard:\n" + "\n".join(
                    [f"{entry['username']}: {entry['score']}" for entry in leaderboard]
                )
                self.send_message(leaderboard_message)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching leaderboard: {e}")
                self.send_message("Error fetching leaderboard. Please try again later.")
        elif command == "/rankings":
            try:
                response = requests.get(f"{self.server_url}/api/multiplayer_rankings", timeout=5)
                response.raise_for_status()
                rankings = response.json()
                rankings_message = "Multiplayer Rankings:\n" + "\n".join(
                    [f"{entry['username']}: {entry['wins']} wins, {entry['losses']} losses" for entry in rankings]
                )
                self.send_message(rankings_message)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching rankings: {e}")
                self.send_message("Error fetching rankings. Please try again later.")
        else:
            self.send_message("Unknown command. Type /help for a list of commands.")
