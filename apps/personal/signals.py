from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, User
from .models import Personal
from django.contrib.auth.signals import user_logged_in
from django.conf import settings

# 💥 OPTIMIZACIÓN: Añadimos (sender, **kwargs) para que sea compatible con post_migrate
def crear_roles_maestros(sender, **kwargs):
    """ Crea los grupos base solo cuando se ejecutan migraciones. """
    roles = [
        'Coordinación', 'Dirección', 'Docentes', 
        'Tutores', 'Secretaría', 'Asistente', 'Auxiliares'
    ]
    for rol in roles:
        Group.objects.get_or_create(name=rol)

@receiver(post_save, sender=Personal)
def procesar_personal_sistema(sender, instance, created, **kwargs):
    """
    Señal unificada y segura (Thread-Safe) para el Control de Personal.
    """
    
    # FASE 1: AUTOMATIZACIÓN DE CUENTA NUEVA
    if created and not instance.user:
        if not User.objects.filter(username=instance.dni).exists():
            nuevo_usuario = User.objects.create_user(
                username=instance.dni,
                password=instance.dni,
                first_name=instance.nombres,
                last_name=instance.apellidos
            )
            
            # 💥 OPTIMIZACIÓN SENIOR (Thread-Safety): 
            # En lugar de desconectar la señal (lo cual es peligroso en producción), 
            # usamos .update() que inyecta la foránea directamente en MySQL sin 
            # disparar nuevamente el post_save.
            Personal.objects.filter(pk=instance.pk).update(user=nuevo_usuario)
            instance.user = nuevo_usuario # Actualizamos la memoria local
            print(f"✅ CUENTA AUTOMÁTICA CREADA: DNI {instance.dni}")

    # FASE 2: ASIGNACIÓN DE ROLES PERIMETRALES
    if instance.user:
        user = instance.user
        
        cargo_a_grupo = {
            'DIR': 'Dirección',
            'COO': 'Coordinación',
            'DOC': 'Docentes',
            'SEC': 'Secretaría',
            'ASI': 'Asistente',
            'AUX': 'Auxiliares',
        }
        
        grupo_nombre = cargo_a_grupo.get(instance.cargo)
        
        if grupo_nombre:
            try:
                grupo = Group.objects.get(name=grupo_nombre)
                
                if not user.groups.filter(id=grupo.id).exists():
                    user.groups.clear()
                    user.groups.add(grupo)
                
                debe_ser_staff = instance.cargo in ['DIR', 'COO']
                if user.is_staff != debe_ser_staff:
                    user.is_staff = debe_ser_staff
                    # 💥 OPTIMIZACIÓN: Solo guardamos la columna 'is_staff' para ganar velocidad
                    user.save(update_fields=['is_staff']) 
                    
            except Group.DoesNotExist:
                pass

@receiver(user_logged_in)
def procesar_mantener_sesion(sender, request, user, **kwargs):
    """
    Configura la caducidad de la cookie de sesión basándose en el Checkbox.
    """
    if request.method == 'POST':
        remember_me = request.POST.get('rememberMe') 
        
        if not remember_me:
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)