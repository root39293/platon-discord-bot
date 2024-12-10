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
                await interaction.response.send_message("이 명령어는 서버에만 사용할 수 있습니다.", ephemeral=True)
                return

            valid_tasks = [task.value.strip() for task in self.tasks if task.value.strip()]
            todos = cog.get_user_todos(str(interaction.user.id), str(interaction.guild.id))
            
            if len(todos) >= 4:  # 최대 4개까지만 추가 가능 (5번째 추가 시도시 경고)
                await interaction.response.send_message("할 일은 최대 4개까지만 등록할 수 있습니다.", ephemeral=True)
                return
            
            for task in valid_tasks:
                if len(todos) >= 4:  # 여러 개 추가 시에도 최대 4개 제한
                    break
                todos.append(TodoItem(task))

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

    @classmethod
    def persistent_view_register(cls, bot):
        """영구적인 View 등록"""
        view = cls([], None)  # 임시 view 생성
        bot.add_view(view)  # 봇에 view 등록

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
            if i >= 4:  # 최대 5개까지만 지원 (row 0은 추가버튼용)
                break
            
            complete_button = TodoButton(i, todo.completed)
            complete_button.callback = self.todo_button_callback
            complete_button.row = i + 1
            self.add_item(complete_button)

            delete_button = Button(
                label="삭제",
                style=discord.ButtonStyle.danger,
                emoji="🗑️",
                custom_id=f"delete_todo_{i}",
                row=i + 1
            )
            delete_button.callback = self.delete_button_callback
            self.add_item(delete_button)

    async def add_button_callback(self, interaction: discord.Interaction):
        modal = AddTodoModal()
        await interaction.response.send_modal(modal)

    async def todo_button_callback(self, interaction: discord.Interaction):
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
        self.todos = {}
        self.weekly_todos = {}
        self.todo_messages = {}  
        self.weekly_todo_messages = {}  
        self.kst = pytz.timezone('Asia/Seoul')
        self.cleanup_task.start()
        
        # View 영구 등록
        WeeklyTodoView.persistent_view_register(bot)
        TodoView.persistent_view_register(bot)

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

    def get_user_weekly_todos(self, user_id: str, guild_id: str) -> dict:
        """사용자의 주간 할 일 목록을 가져옵니다"""
        if guild_id not in self.weekly_todos:
            self.weekly_todos[guild_id] = {}
        if user_id not in self.weekly_todos[guild_id]:
            self.weekly_todos[guild_id][user_id] = {
                'items': [],
                'start_date': datetime.now(self.kst).strftime("%Y-%m-%d")
            }
        return self.weekly_todos[guild_id][user_id]

    def create_weekly_todo_message(self, user: discord.User, weekly_todo_data: dict) -> str:
        """주간 퀘스트 메시지 생성"""
        todos = weekly_todo_data['items']
        start_date = weekly_todo_data['start_date']
        
        if not start_date:
            return "주간 퀘스트가 없습니다."
            
        end_date = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=6)
        today = datetime.now(self.kst).date()
        days_left = (end_date.date() - today).days
        
        message = [
            f"# 📋 {user.display_name}님의 주간퀘스트",
            f"**{start_date} ~ {end_date.strftime('%Y-%m-%d')}**",
            f"**남은 기간**: `D-{days_left if days_left >= 0 else '만료'}`\n"
        ]

        if todos:
            completed = sum(1 for todo in todos if todo["completed"])
            total = len(todos)
            progress = (completed / total) * 100 if total > 0 else 0
            
            message.append(f"**진행률**: `{completed}/{total}` (`{progress:.1f}%`)\n")
            message.append("**📌 퀘스트 목록**")
            for todo in todos:
                if todo["completed"]:
                    message.append(f"> ✅ ~~{todo['content']}~~")
                else:
                    message.append(f"> ⬜ {todo['content']}")
        else:
            message.extend([
                "```md",
                "# 새로운 주간퀘스트가 시작되었습니다!",
                "* '퀘스트 추가' 버튼으로 퀘스트를 추가하세요",
                "* 최대 4개까지 등록 가능",
                "* 7일이 지나면 자동으로 초기화됩니다",
                "```"
            ])

        return "\n".join(message)

    @tasks.loop(time=time(hour=0, minute=0))  
    async def cleanup_task(self):
        """할 일 목록 초기화"""
        self.todos.clear()
        self.todo_messages.clear()  
        logging.info("할 일 목록이 초기화되었습니다.")

    @app_commands.command(name="할일", description="할 일 목록을 관리합니다")
    async def todo(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("이 명령어는 서버에서만 사용할 수 있습니다.", ephemeral=True)
            return
        
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
                    pass 
            except Exception as e:
                logging.error(f"이전 메시지 삭제 중 오류 발생: {e}")

        todos = self.get_user_todos(user_id, guild_id)
        view = TodoView(todos, self)
        content = self.create_todo_message(interaction.user, todos)
        
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
        
        # 이전 메시지 삭제
        if guild_id in self.weekly_todo_messages and user_id in self.weekly_todo_messages[guild_id]:
            try:
                old_message = await interaction.channel.fetch_message(self.weekly_todo_messages[guild_id][user_id])
                await old_message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass  # 메시지가 이미 삭제되었거나 권한이 없는 경우 무시
        
        weekly_todo_data = self.get_user_weekly_todos(user_id, guild_id)
        
        # 주간 퀘스트 만료 체크 및 초기화
        if weekly_todo_data['start_date']:
            start_date = datetime.strptime(weekly_todo_data['start_date'], "%Y-%m-%d")
            end_date = start_date + timedelta(days=6)
            if datetime.now(self.kst).date() > end_date.date():
                weekly_todo_data['start_date'] = datetime.now(self.kst).strftime("%Y-%m-%d")
                weekly_todo_data['items'] = []

        view = WeeklyTodoView(weekly_todo_data['items'], self)
        content = self.create_weekly_todo_message(interaction.user, weekly_todo_data)

        await interaction.response.send_message(content=content, view=view)
        message = await interaction.original_response()
        
        if guild_id not in self.weekly_todo_messages:
            self.weekly_todo_messages[guild_id] = {}
        self.weekly_todo_messages[guild_id][user_id] = message.id

class WeeklyTodoModal(Modal):
    def __init__(self):
        super().__init__(title="주간 퀘스트 추가")
        self.tasks = []
        for i in range(1, 4):
            task = TextInput(
                label=f"퀘스트 {i}",
                placeholder=f"{i}번째 퀘스트를 입력하세요",
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
            guild_id = str(interaction.guild_id)
            user_id = str(interaction.user.id)
            weekly_todo_data = cog.get_user_weekly_todos(user_id, guild_id)

            if len(weekly_todo_data['items']) >= 4:  # 최대 4개까지만 추가 가능
                await interaction.response.send_message("퀘스트는 최대 4개까지만 등록할 수 있습니다.", ephemeral=True)
                return

            for task in valid_tasks:
                if len(weekly_todo_data['items']) >= 4:  # 여러 개 추가 시에도 최대 4개 제한
                    break
                weekly_todo_data['items'].append({"content": task, "completed": False})
            
            view = WeeklyTodoView(weekly_todo_data['items'], cog)
            content = cog.create_weekly_todo_message(interaction.user, weekly_todo_data)
            await interaction.response.edit_message(content=content, view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"퀘스트 추가 중 오류가 발생했습니다: {str(e)}", ephemeral=True)

class WeeklyTodoView(discord.ui.View):
    def __init__(self, todos: list, cog: Todo):
        super().__init__(timeout=None)
        self.todos = todos
        self.cog = cog
        self.setup_view()

    @classmethod
    def persistent_view_register(cls, bot):
        """영구적인 View 등록"""
        view = cls([], None)  # 임시 view 생성
        bot.add_view(view)  # 봇에 view 등록

    def setup_view(self):
        """버튼 레이아웃 설정"""
        self.clear_items()  

        add_button = Button(
            label="퀘스트 추가",
            style=discord.ButtonStyle.green,
            emoji="📝",
            custom_id="add_weekly_todo",
            row=0
        )
        add_button.callback = self.add_todo
        self.add_item(add_button)

        for i, todo in enumerate(self.todos):
            if i >= 4:  # 최대 4개까지만 표시
                break
                
            complete_button = Button(
                style=discord.ButtonStyle.secondary if todo["completed"] else discord.ButtonStyle.success,
                emoji="✅" if todo["completed"] else "⬜",
                custom_id=f"weekly_complete_{i}",
                row=i + 1
            )
            complete_button.callback = self.complete_button_callback
            self.add_item(complete_button)

            delete_button = Button(
                label="삭제",
                style=discord.ButtonStyle.danger,
                emoji="🗑️",
                custom_id=f"weekly_delete_{i}",
                row=i + 1
            )
            delete_button.callback = self.delete_button_callback
            self.add_item(delete_button)

    async def add_todo(self, interaction: discord.Interaction):
        if len(self.todos) >= 4:  # 최대 4개로 제한
            await interaction.response.send_message("퀘스트는 최대 4개까지만 등록할 수 있습니다.", ephemeral=True)
            return
            
        modal = WeeklyTodoModal()
        await interaction.response.send_modal(modal)

    async def complete_button_callback(self, interaction: discord.Interaction):
        """퀘스트 완료/미완료 토글"""
        content = interaction.message.content
        if not content.startswith(f"# 📋 {interaction.user.display_name}님의 주간퀘스트"):
            await interaction.response.send_message("자신의 퀘스트만 수정할 수 있습니다.", ephemeral=True)
            return

        custom_id = interaction.data["custom_id"]
        index = int(custom_id.split("_")[2])
        
        self.todos[index]["completed"] = not self.todos[index]["completed"]
        
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        weekly_todo_data = self.cog.get_user_weekly_todos(user_id, guild_id)
        weekly_todo_data['items'] = self.todos  # 데이터 업데이트
        
        content = self.cog.create_weekly_todo_message(interaction.user, weekly_todo_data)
        view = WeeklyTodoView(self.todos, self.cog)
        await interaction.response.edit_message(content=content, view=view)

    async def delete_button_callback(self, interaction: discord.Interaction):
        """퀘스트 삭제"""
        content = interaction.message.content
        if not content.startswith(f"# 📋 {interaction.user.display_name}님의 주간퀘스트"):
            await interaction.response.send_message("자신의 퀘스트만 삭제할 수 있습니다.", ephemeral=True)
            return

        custom_id = interaction.data["custom_id"]
        index = int(custom_id.split("_")[2])

        del self.todos[index]

        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        weekly_todo_data = self.cog.get_user_weekly_todos(user_id, guild_id)
        weekly_todo_data['items'] = self.todos  # 데이터 업데이트
        
        content = self.cog.create_weekly_todo_message(interaction.user, weekly_todo_data)
        view = WeeklyTodoView(self.todos, self.cog)
        await interaction.response.edit_message(content=content, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Todo(bot))