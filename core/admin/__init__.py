from django.contrib import admin

import messages_extends.admin  # Ensure it got registered.
import messages_extends.models

from .attempt       import *
from .clarification import *
from .compiler      import *
from .contest       import *
from .notification  import *
from .problem       import *


admin.site.unregister(messages_extends.models.Message)
