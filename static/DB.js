let upd_btn = document.getElementById('update-info')
upd_btn.addEventListener("click", function () { Update(); });

function Update(){
    let Request = new XMLHttpRequest();
    let entries = document.getElementById('table-entries').value;
    let Name = document.getElementById('item-name').value;
    let csgo500 = document.getElementById('item-csgo500').value;
    let csgotm = document.getElementById('item-csgotm').value;
    let csgotmv = document.getElementById('item-csgotmv').value;
    let steamtm = document.getElementById('item-steamtm').value;
    let steamtmv = document.getElementById('item-steamtmv').value;
    let last_check = document.getElementById('item-last').value;

    Request.responseType = 'text';
    Request.open("POST", "./items?name=" + Name + "&csgo500=" + csgo500 + "&csgotm=" + csgotm + "&csgotmv=" + csgotmv + "&steamtm=" + steamtm + "&steamtmv=" + steamtmv + "&last_check=" + last_check + "&entries=" + entries, true);
    Request.send();
    Request.onload = function() {
        let table_info = document.getElementById('DB-info');
        table_info.innerHTML = Request.response;
        }}
