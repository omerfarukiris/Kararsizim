// Oy verme: formu fetch ile gönderir ve sayfayı yenilemeden sonuçları gösterir.
// JS kapalıysa form normal POST olarak çalışır (sunucu redirect eder).
(function () {
  "use strict";

  var percentFormat = new Intl.NumberFormat("tr-TR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text; // textContent: HTML kaçışı otomatik
    return node;
  }

  // templates/partials/poll_results.html ile aynı yapıyı üretir.
  function renderResults(data) {
    var list = el("ul", "results");
    list.setAttribute("data-results", "");
    data.results.forEach(function (row) {
      var mine = row.id === data.voted_choice_id;
      var item = el("li", "result result--" + row.order + (mine ? " result--mine" : ""));

      var label = el("div", "result__label");
      var text = el("span", "result__text", row.text + " ");
      if (mine) text.appendChild(el("span", "result__mine", "✓ senin oyun"));
      if (row.leader) text.appendChild(el("span", "result__badge", "👑 önde"));
      label.appendChild(text);
      label.appendChild(el("span", "result__value", "%" + percentFormat.format(row.percent) + " · " + row.votes + " oy"));

      var track = el("div", "result__track");
      var bar = el("div", "result__bar");
      bar.style.width = row.percent + "%";
      track.appendChild(bar);

      item.appendChild(label);
      item.appendChild(track);
      list.appendChild(item);
    });
    return list;
  }

  function showResults(container, data) {
    var poll = container.closest("[data-poll]");
    var total = poll && poll.querySelector("[data-total]");
    if (total) total.textContent = data.total;

    var message = container.querySelector("[data-vote-message]");
    container.textContent = "";
    container.appendChild(renderResults(data));
    if (message) container.appendChild(message);
  }

  function setMessage(container, text) {
    var message = container.querySelector("[data-vote-message]");
    if (message) message.textContent = text || "";
  }

  // Ağ hatasında normal form gönderimine geri dön.
  function fallbackSubmit(form, choiceId) {
    var input = document.createElement("input");
    input.type = "hidden";
    input.name = "choice";
    input.value = choiceId;
    form.appendChild(input);
    HTMLFormElement.prototype.submit.call(form);
  }

  document.addEventListener("submit", function (event) {
    var form = event.target.closest("[data-vote-form]");
    if (!form) return;
    var submitter = event.submitter;
    if (!submitter || submitter.name !== "choice") return; // bilinmeyen durum: normal POST
    event.preventDefault();

    var container = form.closest("[data-poll-choices]");
    var buttons = form.querySelectorAll("button");
    buttons.forEach(function (b) { b.disabled = true; });
    setMessage(container, "");

    var body = new FormData(form);
    body.append("choice", submitter.value);

    fetch(form.action, {
      method: "POST",
      body: body,
      credentials: "same-origin",
      headers: {
        "Accept": "application/json",
        "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value,
      },
    })
      .then(function (response) {
        return response.json().then(function (data) { return { status: response.status, data: data }; });
      })
      .then(function (result) {
        var data = result.data;
        if (data.results) {
          // Başarılı oy (200) ya da daha önce verilmiş oy (409): sonuçları göster.
          showResults(container, data);
          if (!data.ok) setMessage(container, data.error);
        } else {
          buttons.forEach(function (b) { b.disabled = false; });
          setMessage(container, data.error || "Bir şeyler ters gitti, tekrar dener misin?");
        }
      })
      .catch(function () {
        fallbackSubmit(form, submitter.value);
      });
  });
})();
