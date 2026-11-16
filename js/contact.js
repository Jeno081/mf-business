/* MF Business — formulaire de contact */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var form = MF.qs('[data-contact-form]');
    if (!form) return;

    var success = MF.qs('[data-form-success]');
    var nameInput = MF.qs('#c-name');
    var phoneInput = MF.qs('#c-phone');
    var emailInput = MF.qs('#c-email');
    var subjectInput = MF.qs('#c-subject');
    var messageInput = MF.qs('#c-message');

    function setError(input, hasError) {
      var field = input.closest('.field');
      if (!field) return;
      field.classList.toggle('has-error', hasError);
      input.setAttribute('aria-invalid', String(hasError));
    }

    [nameInput, phoneInput, emailInput, messageInput].forEach(function (input) {
      if (!input) return;
      input.addEventListener('input', function () { setError(input, false); });
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var firstInvalid = null;

      var name = nameInput ? nameInput.value.trim() : '';
      if (name.length < 2) { setError(nameInput, true); firstInvalid = firstInvalid || nameInput; }
      else setError(nameInput, false);

      var phone = phoneInput ? phoneInput.value.trim() : '';
      var digits = phone.replace(/[^0-9]/g, '');
      if (digits.length < 8) { setError(phoneInput, true); firstInvalid = firstInvalid || phoneInput; }
      else setError(phoneInput, false);

      var email = emailInput ? emailInput.value.trim() : '';
      if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        setError(emailInput, true);
        firstInvalid = firstInvalid || emailInput;
      } else if (emailInput) setError(emailInput, false);

      var message = messageInput ? messageInput.value.trim() : '';
      if (message.length < 5) { setError(messageInput, true); firstInvalid = firstInvalid || messageInput; }
      else setError(messageInput, false);

      if (firstInvalid) {
        firstInvalid.focus();
        MF.toast('Vérifiez les champs en rouge, puis réessayez.', 'error');
        return;
      }

      var text = 'Bonjour MF Business 👋\n\n' +
        'Nom : ' + name + '\n' +
        'Téléphone : ' + phone + '\n' +
        (email ? 'E-mail : ' + email + '\n' : '') +
        'Sujet : ' + (subjectInput ? subjectInput.value : 'Contact') + '\n\n' +
        'Message :\n' + message;

      var url = MF.whatsappLink(text);
      var win = window.open(url, '_blank', 'noopener');
      if (!win) window.location.href = url;

      if (success) {
        success.classList.add('is-visible');
        success.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      MF.toast('Votre message est prêt dans WhatsApp.', 'success');
    });
  });
})();
