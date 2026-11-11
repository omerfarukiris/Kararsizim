// Anket oluşturma formunda seçenek kutularını dinamik yönetir.
// JS kapalıyken sunucu 5 kutunun hepsini çizer; burada boş fazlalıklar
// kaldırılır, "+ Seçenek ekle" ve "×" butonları eklenir. Asıl doğrulama sunucudadır.
(function () {
  "use strict";

  var list = document.querySelector("[data-choices]");
  if (!list) return;

  var MIN = parseInt(list.dataset.min, 10) || 2;
  var MAX = parseInt(list.dataset.max, 10) || 5;

  function rows() {
    return Array.prototype.slice.call(list.querySelectorAll("[data-choice-row]"));
  }

  // Satırları yeniden numaralandırır, × ve ekle butonlarının durumunu günceller.
  function refresh() {
    var all = rows();
    all.forEach(function (row, i) {
      var n = i + 1;
      var input = row.querySelector("input");
      var label = row.querySelector("label");
      input.id = "choice-" + n;
      input.placeholder = "Seçenek " + n;
      label.htmlFor = input.id;
      label.textContent = "Seçenek " + n;

      var remove = row.querySelector("[data-remove]");
      if (i >= MIN && !remove) {
        remove = document.createElement("button");
        remove.type = "button";
        remove.className = "choice-row__remove";
        remove.setAttribute("data-remove", "");
        remove.textContent = "×";
        row.appendChild(remove);
      } else if (i < MIN && remove) {
        remove.remove();
        remove = null;
      }
      if (remove) remove.setAttribute("aria-label", n + ". seçeneği kaldır");
    });
    addButton.hidden = all.length >= MAX;
  }

  function makeRow() {
    var row = rows()[0].cloneNode(true);
    var input = row.querySelector("input");
    input.value = "";
    var remove = row.querySelector("[data-remove]");
    if (remove) remove.remove();
    return row;
  }

  // Doldurulmuş olanları ve en az MIN satırı tut, gerisini kaldır.
  var keep = Math.max(
    MIN,
    rows().reduce(function (last, row, i) {
      return row.querySelector("input").value.trim() ? i + 1 : last;
    }, 0)
  );
  rows().forEach(function (row, i) {
    if (i >= keep) row.remove();
  });

  var addButton = document.createElement("button");
  addButton.type = "button";
  addButton.className = "button button--ghost button--small";
  addButton.textContent = "+ Seçenek ekle";
  list.insertAdjacentElement("afterend", addButton);

  addButton.addEventListener("click", function () {
    if (rows().length >= MAX) return;
    var row = makeRow();
    list.appendChild(row);
    refresh();
    row.querySelector("input").focus();
  });

  list.addEventListener("click", function (event) {
    var remove = event.target.closest("[data-remove]");
    if (!remove || rows().length <= MIN) return;
    remove.closest("[data-choice-row]").remove();
    refresh();
    addButton.focus();
  });

  refresh();
})();
