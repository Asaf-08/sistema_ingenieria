import urllib.parse
import threading
import requests

class WhatsAppService:
    """
    Servicio centralizado para manejar todas las comunicaciones por WhatsApp del colegio.
    """

    @staticmethod
    def enviar_whatsapp_background(telefono, mensaje):
        """ Viaja por debajo sin congelar la pantalla (Conexión al bot de Node.js) """
        url_bot = "http://localhost:3000/api/enviar-mensaje"
        datos = {
            "telefono": telefono,
            "mensaje": mensaje
        }
        try:
            # Simulamos en consola para tener registro
            print(f"🚀 [WHATSAPP ENVIANDO...] -> Destino: {telefono}")
            # Le damos 5 segundos máximo para intentar conectarse con Node
            requests.post(url_bot, json=datos, timeout=5)
        except Exception as e:
            print(f"❌ Error al enviar WhatsApp a {telefono}: {e}")

    @classmethod
    def enviar_mensaje_api(cls, numero, mensaje):
        """
        NIVEL 2: Envío automático en segundo plano.
        Lanza el envío en un "hilo" paralelo para no hacer esperar al usuario web.
        """
        if numero:
            hilo = threading.Thread(target=cls.enviar_whatsapp_background, args=(numero, mensaje))
            hilo.start()
        return True

    # =========================================================
    # PLANTILLAS DE MENSAJES DEL COLEGIO
    # =========================================================

    @classmethod
    def notificar_nuevo_comunicado(cls, nombre_docente, telefono_docente, titulo_comunicado):
        mensaje = (
            f"📢 *NUEVO COMUNICADO OFICIAL*\n\n"
            f"Hola Prof. {nombre_docente},\n"
            f"La Dirección ha publicado un nuevo aviso: *{titulo_comunicado}*.\n\n"
            f"⚠️ *Acción requerida:*\n"
            f"Por favor, ingrese al sistema para leer el detalle completo.\n\n"
            f"Atte. Administración del Colegio."
        )
        return cls.enviar_mensaje_api(telefono_docente, mensaje)

    @classmethod
    def notificar_material_impreso(cls, nombre_docente, telefono_docente, curso, tema):
        mensaje = (
            f"🖨️ *MATERIALES LISTOS*\n\n"
            f"Hola Prof. {nombre_docente},\n"
            f"Sus copias e impresiones para el curso de *{curso}* ({tema}) ya están listas.\n"
            f"Puede pasar a recogerlas por secretaría.\n\n"
        )
        return cls.enviar_mensaje_api(telefono_docente, mensaje)

    @classmethod
    def notificar_supervision(cls, nombre_docente, telefono_docente):
        mensaje = (
            f"📝 *NUEVA SUPERVISIÓN REGISTRADA*\n\n"
            f"Hola Prof. {nombre_docente},\n"
            f"Se ha registrado una nueva retroalimentación de su clase en el sistema.\n"
            f"Puede revisarla desde su Portal Docente.\n\n"
            f"Atte. Coordinación Académica."
        )
        return cls.enviar_mensaje_api(telefono_docente, mensaje)
    
    @classmethod
    def notificar_revision_evidencia(cls, nombre_docente, telefono_docente, estado, observaciones):
        """
        Dispara el aviso cuando Coordinación aprueba u observa una evidencia/material.
        """
        if estado.upper() == 'APROBADO':
            icono = "✅"
            texto_estado = "*APROBADA*"
        else:
            icono = "⚠️"
            texto_estado = "*OBSERVADA*"

        mensaje = (
            f"{icono} *REVISIÓN DE EVIDENCIA*\n\n"
            f"Hola Prof. {nombre_docente},\n"
            f"Coordinación ha revisado su material y ha sido marcado como {texto_estado}.\n"
        )
        
        if observaciones:
            mensaje += f"\n👁️ *Nota de coordinación:* {observaciones}\n"
            
        mensaje += f"\n👉 Ingrese al sistema para más detalles.\nAtte. Coordinación Académica."
        
        return cls.enviar_mensaje_api(telefono_docente, mensaje)

    @classmethod
    def notificar_falta_material(cls, nombre_docente, telefono_docente):
        mensaje = (
            f"⚠️ *RECORDATORIO DE MATERIALES*\n\n"
            f"Hola Prof. {nombre_docente}, el sistema detecta que aún no ha subido sus materiales de la semana.\n"
            f"Le recordamos que el plazo límite son los días *jueves*.\n"
            f"Por favor, ingrese al sistema a la brevedad para regularizar su envío.\n\n"
            f"Atte. Coordinación.\n\n"
            
            f"_Si ya ha enviado sus materiales, por favor ignore este mensaje._"
        )
        return cls.enviar_mensaje_api(telefono_docente, mensaje)
    
    @classmethod
    def alerta_tutor_riesgo(cls, nombre_tutor, telefono_tutor, grado, seccion, cantidad_riesgo):
        mensaje = (
            f"⚠️ *ALERTA DE RENDIMIENTO*\n\n"
            f"Hola Prof. {nombre_tutor},\n"
            f"El motor de Inteligencia Artificial detecta que *{cantidad_riesgo} alumno(s)* de su aula ({grado} {seccion}) presentan una tendencia a la baja o riesgo crítico esta semana.\n\n"
            f"👉 Por favor, ingrese al sistema para ver el diagnóstico detallado y aplicar acciones preventivas.\n"
            f"Atte. Coordinación Académica."
        )
        return cls.enviar_mensaje_api(telefono_tutor, mensaje)

    @classmethod
    def alerta_tutor_exito(cls, nombre_tutor, telefono_tutor, grado, seccion):
        mensaje = (
            f"🌟 *REPORTE DE TUTORÍA*\n\n"
            f"Hola Prof. {nombre_tutor},\n"
            f"¡Excelente trabajo! El análisis de esta semana indica que ningún alumno de su aula ({grado} {seccion}) presenta riesgo académico.\n\n"
            f"Sigan con el buen ritmo. Feliz fin de semana.\n"
            f"Atte. Coordinación Académica."
        )
        return cls.enviar_mensaje_api(telefono_tutor, mensaje)