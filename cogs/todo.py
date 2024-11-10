# todo.py
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import json
import os
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Optional
import asyncio
from discord.ext import tasks

class AddTodoModal(Modal):
    def __init__(self):
        super().__init__(title="할 일 추가")
        self.tasks = []
        for i in range(1, 4):
            task = TextInput(
                label=f"할 일 {i}",
                placeholder=f"{i}번째 할 일을 입력하세요",
                required=i == 1,  # 첫 번째 할 일만 필수
                max_length=100
            )
            self.tasks.append(task)
            self.add_item(task)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            cog = interaction.client.get_cog('Todo')
            if not cog:
                await interaction.response.send_message("오류가 발생했습니다.", ephemeral=True)
                return

            if not interaction.guild:
                await interaction.response.send_message("이 명령어는 서버에서만 사용할 수 있습니다.", ephemeral=True)
                return

            # 입력된 할 일만 필터링
            valid_tasks = [task.value.strip() for task in self.tasks if task.value.strip()]
            
            # 현재 할 일 목록 불러오기
            todos = cog.todo_manager.load_todos(
                str(interaction.user.id),
                str(interaction.guild.id)
            )
            today = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d")
            
            # 오늘의 할 일만 필터링
            todos = [todo for todo in todos if todo.created_at == today]
            
            # 새로운 할 일 추가
            for task in valid_tasks:
                todos.append(TodoItem(task))
            
            # 저장
            cog.todo_manager.save_todos(
                str(interaction.user.id),
                str(interaction.guild.id),
                todos
            )
            
            # 뷰 업데이트
            view = TodoView(todos, cog)
            content = cog.create_todo_message(interaction.user, todos)
            await interaction.response.edit_message(content=content, view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"할 일 추가 중 오류가 발생했습니다: {str(e)}", ephemeral=True)

class TodoItem:
    def __init__(self, task: str, created_at: str = None):
        self.task = task
        self.completed = False
        self.created_at = created_at or datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d")

    def to_dict(self) -> Dict:
        return {
            "task": self.task,
            "completed": self.completed,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TodoItem':
        item = cls(data["task"], data["created_at"])
        item.completed = data["completed"]
        return item

class TodoButton(Button):
    def __init__(self, todo_id: int, is_complete: bool):
        super().__init__(
            style=discord.ButtonStyle.secondary if is_complete else discord.ButtonStyle.success,
            emoji="✅" if is_complete else "⬜",
            custom_id=f"todo_{todo_id}",
            row=(todo_id // 5) + 1  # 5개씩 한 줄에 표시 (row 0은 추가 버튼용)
        )

class TodoView(View):
    def __init__(self, todos: List[TodoItem], cog):
        super().__init__(timeout=None)
        self.todos = todos
        self.cog = cog
        self.setup_view()

    def setup_view(self):
        self.clear_items()
        
        add_button = Button(
            label="할 일 추가하기",
            style=discord.ButtonStyle.primary,
            emoji="📝",
            custom_id="add_todo",
            row=0
        )
        add_button.callback = self.add_button_callback
        self.add_item(add_button)

        for i, todo in enumerate(self.todos):
            button = TodoButton(i, todo.completed)
            button.callback = self.todo_button_callback
            self.add_item(button)

    async def add_button_callback(self, interaction: discord.Interaction):
        modal = AddTodoModal()
        await interaction.response.send_modal(modal)

    async def todo_button_callback(self, interaction: discord.Interaction):
        custom_id = interaction.data["custom_id"]
        index = int(custom_id.split("_")[1])
        
        self.todos[index].completed = not self.todos[index].completed
        self.cog.todo_manager.save_todos(
            str(interaction.user.id),
            str(interaction.guild.id),
            self.todos
        )
        
        view = TodoView(self.todos, self.cog)
        content = self.cog.create_todo_message(interaction.user, self.todos)
        await interaction.response.edit_message(content=content, view=view)

class TodoManager:
    def __init__(self, file_path: str):
        self.file_path = os.path.join(os.path.dirname(__file__), '..', file_path)
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self.ensure_file_exists()

    def ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)

    def load_todos(self, user_id: str, guild_id: str) -> List[TodoItem]:
        with open(self.file_path, "r", encoding='utf-8') as f:
            data = json.load(f)
            # guild_id > user_id 구조로 변경
            guild_data = data.get(guild_id, {})
            user_todos = guild_data.get(user_id, [])
            return [TodoItem.from_dict(todo) for todo in user_todos]

    def save_todos(self, user_id: str, guild_id: str, todos: List[TodoItem]):
        with open(self.file_path, "r+", encoding='utf-8') as f:
            data = json.load(f)
            
            # 서버 데이터 가져오기
            guild_data = data.get(guild_id, {})
            
            # 기존 할 일 목록 가져오기
            existing_todos = guild_data.get(user_id, [])
            
            today = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d")
            
            # 오늘의 할 일이 아닌 항목들만 유지
            other_todos = [todo for todo in existing_todos if isinstance(todo, dict) and todo.get('created_at') != today]
            
            # 새로운 할 일 목록과 합치기
            guild_data[user_id] = other_todos + [todo.to_dict() for todo in todos]
            data[guild_id] = guild_data
            
            f.seek(0)
            f.truncate()
            json.dump(data, f, ensure_ascii=False, indent=4)

    def cleanup_old_todos(self):
        """7일 이상 지난 할 일 삭제"""
        with open(self.file_path, "r+", encoding='utf-8') as f:
            data = json.load(f)
            
            # 7일 전 날 계산
            week_ago = (datetime.now(pytz.timezone('Asia/Seoul')) - timedelta(days=7)).strftime("%Y-%m-%d")
            
            # 각 사용자의 할 일 정리
            for user_id in data:
                data[user_id] = [
                    todo for todo in data[user_id] 
                    if isinstance(todo, dict) and todo.get('created_at', '') > week_ago
                ]
            
            # 파일 업데이트
            f.seek(0)
            f.truncate()
            json.dump(data, f, ensure_ascii=False, indent=4)

class Todo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.todo_manager = TodoManager("data/todos.json")
        self.bot.add_view(TodoView([], self))
        self.cleanup_task.start()  # 정리 작업 시작

    def cog_unload(self):
        self.cleanup_task.cancel()  # 작업 중단

    @tasks.loop(hours=24)  # 24시간마다 실행
    async def cleanup_task(self):
        """매일 자정에 7일 이상 지난 할 일 삭제"""
        self.todo_manager.cleanup_old_todos()

    @cleanup_task.before_loop
    async def before_cleanup(self):
        """봇이 시작되면 다음 자정까지 대기"""
        await self.bot.wait_until_ready()
        now = datetime.now(pytz.timezone('Asia/Seoul'))
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep((next_midnight - now).total_seconds())

    @app_commands.command(name="todo", description="할 일 관리")
    async def todo(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("이 명령어는 서버에서만 사용할 수 있습니다.", ephemeral=True)
            return
        
        todos = self.todo_manager.load_todos(
            str(interaction.user.id), 
            str(interaction.guild.id)
        )
        today = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d")
        
        # 오늘의 할 일만 필터링
        todos = [todo for todo in todos if todo.created_at == today]
        
        view = TodoView(todos, self)
        
        # 메시지 생성
        content = self.create_todo_message(interaction.user, todos)
        
        await interaction.response.send_message(content=content, view=view)

    def create_todo_message(self, user: discord.User, todos: List[TodoItem]) -> str:
        today = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y년 %m월 %d일")
        
        message = [
            f"# 📋 {user.display_name}님의 할 일",
            f"**{today}**\n"
        ]

        if todos:
            # 진행 상황
            completed = sum(1 for todo in todos if todo.completed)
            total = len(todos)
            progress = (completed / total) * 100 if total > 0 else 0
            
            message.append(f"**진행률**: `{completed}/{total}` (`{progress:.1f}%`)\n")

            # 모든 할 일을 한 섹션에 표시
            message.append("**📌 할 일 목록**")
            for todo in todos:
                if todo.completed:
                    message.append(f"> ✅ ~~{todo.task}~~")
                else:
                    message.append(f"> ⬜ {todo.task}")
        else:
            message.extend([
                "```md",
                "# 새로운 하루가 시작되었습니다!",
                "* '할 일 추가하기' 버튼으로 할 일을 추가하세요",
                "* 하루에 최대 19개까지 등록 가능",
                "* 매일 자정에 새로운 목록이 시작됩니다",
                "```"
            ])

        return "\n".join(message)

async def setup(bot: commands.Bot):
    await bot.add_cog(Todo(bot))