# todo.py
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from datetime import datetime, time, timedelta
import pytz
from typing import List, Dict
from discord.ext import tasks
import logging

class AddTodoModal(Modal):
    def __init__(self):
        super().__init__(title="할 일 추가")
        self.tasks = []
        for i in range(1, 4):
            task = TextInput(
                label=f"할 일 {i}",
                placeholder=f"{i}번째 할 일을 입력하세요",
                required=i == 1,
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

            valid_tasks = [task.value.strip() for task in self.tasks if task.value.strip()]
            todos = cog.get_user_todos(str(interaction.user.id), str(interaction.guild.id))
            
            # 새로운 할 일 추가
            for task in valid_tasks:
                todos.append(TodoItem(task))
            
            # 메모리에 저장
            cog.save_user_todos(str(interaction.user.id), str(interaction.guild.id), todos)
            
            view = TodoView(todos, cog)
            content = cog.create_todo_message(interaction.user, todos)
            await interaction.response.edit_message(content=content, view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"할 일 추가 중 오류가 발생했습니다: {str(e)}", ephemeral=True)

class TodoItem:
    def __init__(self, task: str):
        self.task = task
        self.completed = False
        self.created_at = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d")

class TodoButton(Button):
    def __init__(self, todo_id: int, is_complete: bool):
        super().__init__(
            style=discord.ButtonStyle.secondary if is_complete else discord.ButtonStyle.success,
            emoji="✅" if is_complete else "⬜",
            custom_id=f"todo_{todo_id}",
            row=(todo_id // 5) + 1
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
            # 완료 버튼
            complete_button = TodoButton(i, todo.completed)
            complete_button.callback = self.todo_button_callback
            complete_button.row = i + 1  # 각 할 일마다 새로운 행
            self.add_item(complete_button)

            # 삭제 버튼
            delete_button = Button(
                label="삭제",
                style=discord.ButtonStyle.danger,
                emoji="🗑️",
                custom_id=f"delete_todo_{i}",
                row=i + 1  # 완료 버튼과 같은 행
            )
            delete_button.callback = self.delete_button_callback
            self.add_item(delete_button)

    async def add_button_callback(self, interaction: discord.Interaction):
        modal = AddTodoModal()
        await interaction.response.send_modal(modal)

    async def todo_button_callback(self, interaction: discord.Interaction):
        # 할 일 목록 소유자 확인
        content = interaction.message.content
        if not content.startswith(f"# 📋 {interaction.user.display_name}님의 할 일"):
            await interaction.response.send_message("자신의 할 일만 수정할 수 있습니다.", ephemeral=True)
            return

        custom_id = interaction.data["custom_id"]
        index = int(custom_id.split("_")[1])
        
        self.todos[index].completed = not self.todos[index].completed
        self.cog.save_user_todos(
            str(interaction.user.id),
            str(interaction.guild.id),
            self.todos
        )
        
        view = TodoView(self.todos, self.cog)
        content = self.cog.create_todo_message(interaction.user, self.todos)
        await interaction.response.edit_message(content=content, view=view)

    async def delete_button_callback(self, interaction: discord.Interaction):
        custom_id = interaction.data["custom_id"]
        index = int(custom_id.split("_")[2])
        
        # 할 일 삭제
        del self.todos[index]
        self.cog.save_user_todos(
            str(interaction.user.id),
            str(interaction.guild.id),
            self.todos
        )
        
        view = TodoView(self.todos, self.cog)
        content = self.cog.create_todo_message(interaction.user, self.todos)
        await interaction.response.edit_message(content=content, view=view)

class Todo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.todos = {}  # 일일 할 일
        self.weekly_todos = {}  # 주간 할 일
        self.todo_messages = {}  # 일일 할 일 메시지
        self.weekly_todo_messages = {}  # 주간 할 일 메시지
        self.kst = pytz.timezone('Asia/Seoul')
        self.cleanup_task.start()

    def get_user_todos(self, user_id: str, guild_id: str) -> List[TodoItem]:
        """유저의 할 일 목록 조회"""
        guild_todos = self.todos.get(guild_id, {})
        user_todos = guild_todos.get(user_id, [])
        today = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d")
        return [todo for todo in user_todos if todo.created_at == today]

    def save_user_todos(self, user_id: str, guild_id: str, todos: List[TodoItem]):
        """유저의 할 일 목록 저장"""
        if guild_id not in self.todos:
            self.todos[guild_id] = {}
        self.todos[guild_id][user_id] = todos

    def get_user_weekly_todos(self, user_id: str, guild_id: str) -> list:
        """사용자의 주간 할 일 목록을 가져옵니다"""
        if guild_id not in self.weekly_todos:
            self.weekly_todos[guild_id] = {}
        if user_id not in self.weekly_todos[guild_id]:
            self.weekly_todos[guild_id][user_id] = {
                'items': [],
                'start_date': None
            }
        return self.weekly_todos[guild_id][user_id]

    def create_weekly_todo_message(self, user: discord.User, weekly_todo_data: dict) -> str:
        """주간 할 일 메시지를 생성합니다"""
        todos = weekly_todo_data['items']
        start_date = weekly_todo_data['start_date']
        
        if not start_date:
            return "주간 할 일이 없습니다."
            
        end_date = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=6)
        today = datetime.now(self.kst).date()
        days_left = (end_date.date() - today).days
        
        status = "🟢 진행중" if days_left >= 0 else "🔴 만료됨"
        period = f"{start_date} ~ {end_date.strftime('%Y-%m-%d')}"
        remaining = f"D-{days_left}" if days_left >= 0 else "만료"
        
        header = f"📅 {user.display_name}님의 주간 할 일\n"
        header += f"기간: {period} ({remaining})\n"
        header += f"상태: {status}\n"
        header += "─" * 30 + "\n"

        if not todos:
            return header + "등록된 할 일이 없습니다."

        todo_list = ""
        for i, todo in enumerate(todos, 1):
            status = "✅" if todo["completed"] else "⬜"
            todo_list += f"{status} {i}. {todo['content']}\n"

        return header + todo_list

    @tasks.loop(time=time(hour=0, minute=0))  # 매일 자정
    async def cleanup_task(self):
        """할 일 목록 초기화"""
        self.todos.clear()
        self.todo_messages.clear()  # 메시지 ID도 초기화
        logging.info("할 일 목록이 초기화되었습니다.")

    @app_commands.command(name="할일", description="할 일 목록을 관리합니다")
    async def todo(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("이 명령어는 서버에서만 사용할 수 있습니다.", ephemeral=True)
            return
        
        # 이전 메시지 삭제
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        if guild_id in self.todo_messages and user_id in self.todo_messages[guild_id]:
            try:
                old_message_id = self.todo_messages[guild_id][user_id]
                channel = interaction.channel
                try:
                    old_message = await channel.fetch_message(old_message_id)
                    await old_message.delete()
                except discord.NotFound:
                    pass  # 메시지가 이미 삭제된 경우
            except Exception as e:
                logging.error(f"이전 메시지 삭제 중 오류 발생: {e}")

        todos = self.get_user_todos(user_id, guild_id)
        view = TodoView(todos, self)
        content = self.create_todo_message(interaction.user, todos)
        
        # 새 메시지 전송 및 ID 저장
        response = await interaction.response.send_message(content=content, view=view)
        message = await interaction.original_response()
        
        if guild_id not in self.todo_messages:
            self.todo_messages[guild_id] = {}
        self.todo_messages[guild_id][user_id] = message.id

    def create_todo_message(self, user: discord.User, todos: List[TodoItem]) -> str:
        today = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y년 %m월 %d일")
        
        message = [
            f"# 📋 {user.display_name}님의 할 일",
            f"**{today}**\n"
        ]

        if todos:
            completed = sum(1 for todo in todos if todo.completed)
            total = len(todos)
            progress = (completed / total) * 100 if total > 0 else 0
            
            message.append(f"**진행률**: `{completed}/{total}` (`{progress:.1f}%`)\n")
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

    @app_commands.command(name="주간퀘", description="메이플 주간퀘스트 체크리스트")
    async def weekly_todo(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("이 명령어는 서버에서만 사용할 수 있습니다.", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        weekly_todo_data = self.get_user_weekly_todos(user_id, guild_id)
        
        # 활성화된 주간 할 일이 없거나 만료된 경우 새로 시작
        if not weekly_todo_data['start_date']:
            weekly_todo_data['start_date'] = datetime.now(self.kst).strftime("%Y-%m-%d")
        else:
            start_date = datetime.strptime(weekly_todo_data['start_date'], "%Y-%m-%d")
            end_date = start_date + timedelta(days=6)
            if datetime.now(self.kst).date() > end_date.date():
                weekly_todo_data['start_date'] = datetime.now(self.kst).strftime("%Y-%m-%d")
                weekly_todo_data['items'] = []  # 만료된 할 일 초기화

        view = WeeklyTodoView(weekly_todo_data['items'], self)
        content = self.create_weekly_todo_message(interaction.user, weekly_todo_data)
        
        # 이전 메시지가 있으면 업데이트, 없으면 새로 생성
        if guild_id in self.weekly_todo_messages and user_id in self.weekly_todo_messages[guild_id]:
            try:
                old_message = await interaction.channel.fetch_message(self.weekly_todo_messages[guild_id][user_id])
                await old_message.edit(content=content, view=view)
                await interaction.response.send_message("주간 할 일 목록을 업데이트했습니다.", ephemeral=True)
                return
            except discord.NotFound:
                pass

        # 새 메시지 전송
        response = await interaction.response.send_message(content=content, view=view)
        message = await interaction.original_response()
        
        if guild_id not in self.weekly_todo_messages:
            self.weekly_todo_messages[guild_id] = {}
        self.weekly_todo_messages[guild_id][user_id] = message.id

class WeeklyTodoView(discord.ui.View):
    def __init__(self, todos: list, cog: Todo):
        super().__init__(timeout=None)
        self.todos = todos
        self.cog = cog

    @discord.ui.button(label="할 일 추가", style=discord.ButtonStyle.green, custom_id="add_weekly_todo")
    async def add_todo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.todos) >= 19:
            await interaction.response.send_message("할 일은 최대 19개까지만 등록할 수 있습니다.", ephemeral=True)
            return
            
        modal = TodoModal(title="주간 할 일 추가")
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.todo_content:
            self.todos.append({"content": modal.todo_content, "completed": False})
            guild_id = str(interaction.guild_id)
            user_id = str(interaction.user.id)
            weekly_todo_data = self.cog.get_user_weekly_todos(user_id, guild_id)
            content = self.cog.create_weekly_todo_message(interaction.user, weekly_todo_data)
            await interaction.message.edit(content=content, view=self)

    # 완료 및 삭제 버튼도 일일 할 일과 동일한 방식으로 구현
    # (코드 생략)

async def setup(bot: commands.Bot):
    await bot.add_cog(Todo(bot))