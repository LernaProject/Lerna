from django.views.generic       import TemplateView

from achievements.models import Achievement
from users.models        import User

class AchievementsView(TemplateView):
    template_name = 'achievements/achievements.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs['user_id']

        user = User.objects.get(id=user_id)

        achievements = Achievement.objects.all()
        unlocked = []
        locked = []
        for achievement in achievements:
            status = achievement.status(user)
            if status.unlocked:
                unlocked.append(status)
            else:
                locked.append(status)

        context.update(
            user=user,
            unlocked=unlocked,
            locked=locked
        )
        return context
