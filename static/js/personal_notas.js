// 💥 TERCERA REGLA DE ORO: PARCHE DE SEGURIDAD
function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Extracción segura del Token
function getCSRFToken() {
    const tokenInput = document.getElementById('csrfToken');
    return tokenInput ? tokenInput.value : '';
}

$(document).ready(function() {
      
      // 1. REVISAR SI HAY NOTAS PENDIENTES Y PINTARLAS AL ENTRAR
      actualizarBotonSincronizacion();
      restaurarValoresOffline(); // 💥 NUEVA FUNCIÓN: Pinta las notas guardadas en el celular

      // 💥 LÓGICA PARA RECUPERAR LO QUE SE QUEDÓ EN EL CELULAR
      function restaurarValoresOffline() {
          let pendientes = JSON.parse(localStorage.getItem('notas_pendientes_tesis')) || {};
          
          // Recorremos las notas que no han subido a internet
          for (let notaId in pendientes) {
              let inputElement = $('#input-nota-' + notaId);
              
              if (inputElement.length) {
                  // Reemplazamos la nota de la Base de Datos por la nota Offline
                  inputElement.val(pendientes[notaId]);
                  // Pintamos el borde de Naranja Fuerte para que sepa que NO ESTÁ GUARDADA AÚN
                  inputElement.removeClass('border-danger border-success border-info').addClass('border-warning');
              }
          }
      }

      // 2. DETECTORES NATIVOS DE INTERNET DEL NAVEGADOR
      window.addEventListener('online', function() {
          Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Conexión a internet restaurada', showConfirmButton: false, timer: 2000 });
          actualizarBotonSincronizacion();
      });

      window.addEventListener('offline', function() {
          Swal.fire({ toast: true, position: 'top-end', icon: 'warning', title: 'Sin conexión a internet. Modo Offline activado.', showConfirmButton: false, timer: 3000 });
      });

      $('#btn-sincronizar-notas').on('click', sincronizarNotasPendientes);

      // ==============================================================
      // FUNCIÓN MAESTRA PARA GUARDAR LA NOTA (CON INTELIGENCIA OFFLINE)
      // ==============================================================
      async function guardarNotaBD(notaId, valor, inputElement) {
          let valorString = String(valor).trim();

          if(valorString !== '' && Number(valorString) < 10 && valorString.length === 1) {
              valorString = '0' + valorString;
              inputElement.val(valorString);
          }

          if (valorString !== '' && (Number(valorString) < 0 || Number(valorString) > 20)) {
              Swal.fire({ icon: 'warning', title: 'Nota inválida', text: 'La calificación debe estar entre 0 y 20.', toast: true, position: 'top-end', showConfirmButton: false, timer: 2000 });
              inputElement.val('');
              inputElement.addClass('border-danger');
              return;
          }

          // 💥 ESCUDO OFFLINE: Si no hay internet, guardar directamente en el celular
          if (!navigator.onLine) {
              guardarEnMemoriaLocal(notaId, valorString);
              // Borde Naranja (Pendiente de subir)
              inputElement.removeClass('border-danger border-success border-info').addClass('border-warning');
              return;
          }

          // Efecto visual: procesando (borde azul)
          inputElement.removeClass('border-danger border-success border-warning').addClass('border-info');

          try {
              const params = new URLSearchParams();
              params.append('nota_id', notaId);
              params.append('valor', valorString);

              const response = await fetch("/personal/notas/guardar/", {
                  method: 'POST',
                  headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCSRFToken() },
                  body: params
              });
              
              const data = await response.json();

              if (data.status === 'ok' || data.success) {
                  // Éxito: Borde Verde
                  inputElement.removeClass('border-info border-warning').addClass('border-success');
                  // Si esta nota estaba pendiente en el celular, la borramos porque ya subió
                  eliminarDeMemoriaLocal(notaId);
              } else {
                  inputElement.removeClass('border-info').addClass('border-danger');
                  Swal.fire({ icon: 'error', title: 'Atención', text: escapeHTML(data.message), toast: true, position: 'top-end', showConfirmButton: false, timer: 3000 });
              }
          } catch (error) {
              // Si falla porque el internet se cortó un segundo después de hacer clic
              guardarEnMemoriaLocal(notaId, valorString);
              inputElement.removeClass('border-info').addClass('border-warning');
          }
      }

      // ==============================================================
      // SISTEMA DE BANDEJA DE SALIDA (LOCAL STORAGE)
      // ==============================================================
      function guardarEnMemoriaLocal(notaId, valor) {
          // Leer la memoria del celular
          let pendientes = JSON.parse(localStorage.getItem('notas_pendientes_tesis')) || {};
          pendientes[notaId] = valor;
          // Guardar de nuevo
          localStorage.setItem('notas_pendientes_tesis', JSON.stringify(pendientes));
          actualizarBotonSincronizacion();
          
          Swal.fire({ toast: true, position: 'top-end', icon: 'info', title: 'Nota retenida en el dispositivo', showConfirmButton: false, timer: 1500 });
      }

      function eliminarDeMemoriaLocal(notaId) {
          let pendientes = JSON.parse(localStorage.getItem('notas_pendientes_tesis')) || {};
          if (pendientes[notaId]) {
              delete pendientes[notaId];
              localStorage.setItem('notas_pendientes_tesis', JSON.stringify(pendientes));
              actualizarBotonSincronizacion();
          }
      }

      function actualizarBotonSincronizacion() {
          let pendientes = JSON.parse(localStorage.getItem('notas_pendientes_tesis')) || {};
          let cantidad = Object.keys(pendientes).length;
          let btn = $('#btn-sincronizar-notas');
          let badge = $('#badge-sincronizacion');

          if (cantidad > 0) {
              btn.removeClass('d-none');
              badge.text(cantidad);
          } else {
              btn.addClass('d-none');
          }
      }

      async function sincronizarNotasPendientes() {
          if (!navigator.onLine) {
              Swal.fire('Atención', 'Aún no tienes conexión a internet para enviar las notas.', 'warning');
              return;
          }

          let pendientes = JSON.parse(localStorage.getItem('notas_pendientes_tesis')) || {};
          let llaves = Object.keys(pendientes);

          if (llaves.length === 0) return;

          Swal.fire({ title: 'Subiendo notas retenidas...', allowOutsideClick: false, didOpen: () => { Swal.showLoading(); }});

          let errores = 0;
          
          // Enviamos una por una al servidor
          for (let notaId of llaves) {
              let valor = pendientes[notaId];
              try {
                  const params = new URLSearchParams();
                  params.append('nota_id', notaId);
                  params.append('valor', valor);

                  const response = await fetch("/personal/notas/guardar/", {
                      method: 'POST',
                      headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCSRFToken() },
                      body: params
                  });
                  const data = await response.json();
                  
                  if (data.status === 'ok' || data.success) {
                      delete pendientes[notaId]; 
                      $('#input-nota-' + notaId).removeClass('border-warning').addClass('border-success');
                  } else {
                      errores++;
                  }
              } catch (e) {
                  errores++;
              }
          }

          // Guardamos lo que haya quedado (si fallaron algunas)
          localStorage.setItem('notas_pendientes_tesis', JSON.stringify(pendientes));
          actualizarBotonSincronizacion();

          if (errores === 0) {
            // 💥 Cambiado a notificación flotante (Toast)
            mostrarNotificacionExito('¡Sincronización Completa! Notas a salvo en el servidor.');
            } else {
                // El error sí lo dejamos como modal porque requiere atención del usuario
                Swal.fire('Advertencia', `Se subieron algunas notas, pero ${errores} fallaron. Intenta presionar el botón de nuevo.`, 'warning');
            }
      }

      // ==============================================================
      // EVENTOS DE LA INTERFAZ
      // ==============================================================
      $('.input-nota').on('blur', function() {
          let inputElement = $(this);
          guardarNotaBD(inputElement.data('nota-id'), inputElement.val(), inputElement);
      });

      $('.btn-nota-rapida').on('click', function() {
          let notaId = $(this).data('id');
          let inputElement = $('#input-nota-' + notaId);

          // 💥 SEGURIDAD FRONTEND: Si el candado está cerrado, bloqueamos el clic
        if (inputElement.prop('disabled')) {
            Swal.fire('Registro Cerrado', 'No puedes modificar notas porque el bimestre ya fue enviado a coordinación.', 'info');
            return; // Corta la ejecución de la función aquí mismo
        }

        let valorSeleccionado = $(this).data('val');
          
        inputElement.val(valorSeleccionado);
        
        let boton = $(this);
        boton.removeClass('border-secondary text-secondary').addClass('bg-dark text-white');
        setTimeout(() => {
            boton.removeClass('bg-dark text-white').addClass('border-secondary text-secondary');
        }, 400);

        guardarNotaBD(notaId, valorSeleccionado, inputElement);
      });
});