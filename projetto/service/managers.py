from django.apps import apps
from django.contrib.auth.models import UserManager as BaseUserManager

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, password=None, **extra_fields):
        """
        Create and save a user with the given username and optional password.
        """
        if not username:
            raise ValueError('The given username must be set')

        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        
        if password is not None:
            user.set_password(password)
        
        user.save(using=self._db)
        
        return user

    def create_user(self, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        sms_verified = extra_fields.get('sms_verified', False)
        
        if sms_verified:
            return self._create_user(username, None, **extra_fields)
        else:
            if password is None:
                raise ValueError('A password is required for user creation')
            return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, password, **extra_fields)
