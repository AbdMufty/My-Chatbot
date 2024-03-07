import json
from difflib import get_close_matches
from hashlib import sha256
import os

class UserManager:
    def __init__(self, user_accounts_file, conversation_history_folder):
        self.user_accounts_file = user_accounts_file
        self.conversation_history_folder = conversation_history_folder
        self.user_accounts = self.load_user_accounts()
        self.current_user = None
        self.conversation_history = {}

    def load_user_accounts(self):
        try:
            with open(self.user_accounts_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_user_accounts(self):
        with open(self.user_accounts_file, 'w') as file:
            json.dump(self.user_accounts, file, indent=2)

    def create_account(self, username, password):
        hashed_password = self.hash_password(password)
        self.user_accounts[username] = hashed_password
        self.save_user_accounts()

    def authenticate_user(self, username, password):
        hashed_password = self.hash_password(password)
        return username in self.user_accounts and self.user_accounts[username] == hashed_password

    def hash_password(self, password):
        return sha256(password.encode('utf-8')).hexdigest()

    def load_conversation_history(self, username):
        user_history_file = os.path.join(self.conversation_history_folder, f'{username}_conversation_history.json')
        try:
            with open(user_history_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    def save_conversation_history(self, username, conversation):
        user_history_file = os.path.join(self.conversation_history_folder, f'{username}_conversation_history.json')
        with open(user_history_file, 'w') as file:
            json.dump(conversation, file, indent=2)

    def add_to_conversation_history(self, username, message):
        if username not in self.conversation_history:
            self.conversation_history[username] = []
        self.conversation_history[username].append(message)
        self.save_conversation_history(username, self.conversation_history[username])


def load_knowledge_base(file_path: str):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"questions": []}

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def find_best_match(user_question: str, questions: list[str]) -> str | None:
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_answer_for_question(question: str, knowledge_base: dict) -> str | None:
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]
    return None

def chatbot(user_manager, knowledge_base):

    conversation_history = user_manager.load_conversation_history(user_manager.current_user)
    for message in conversation_history:
        print(message)

    while True:
        user_input = input("You: ")

        if user_input.lower() == 'exit':
            break

        user_manager.add_to_conversation_history(user_manager.current_user, f"{user_manager.current_user}: {user_input}")

        best_match = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])

        if best_match:
            answer = get_answer_for_question(best_match, knowledge_base)
            print(f"Bot: {answer}")
        else:
            print("Bot: I don't know the answer. Can you teach me?")
            new_answer = input("Type the answer or 'skip' to skip: ")

            if new_answer.lower() != 'skip':
                knowledge_base["questions"].append({"question": user_input, "answer": new_answer})
                save_knowledge_base('knowledge_base.json', knowledge_base)
                print("Bot: Thank you! I've learned something new.")

                user_manager.add_to_conversation_history("Bot", f"Bot: Thank you! I've learned something new.")

        user_manager.save_conversation_history("Bot", user_manager.conversation_history.get("Bot", []))

if __name__ == "__main__":
    user_manager = UserManager("user_accounts.json", "conversation_history")

    os.makedirs(user_manager.conversation_history_folder, exist_ok=True)

    knowledge_base = load_knowledge_base("knowledge_base.json")

    username = input("Enter your username: ")

    if username not in user_manager.user_accounts:
        create_account_choice = input("User does not exist. Do you want to create a new account? (yes/no): ")
        if create_account_choice.lower() == 'yes':
            password = input("Enter your password: ")
            user_manager.create_account(username, password)
            print("Account created successfully.")
        else:
            print("Exiting.")
            exit()
    else:
        for attempt in range(3):
            password = input("Enter your password: ")
            if user_manager.authenticate_user(username, password):
                print(f"Welcome back, {username}!")
                break
            else:
                print(f"Incorrect password. {2 - attempt} attempts remaining.")
        else:
            print("Maximum attempts reached. Exiting.")
            exit()

    user_manager.current_user = username
    chatbot(user_manager, knowledge_base)