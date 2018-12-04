var showTime = true;

function changeShowTimeState() {
    var i;

    showTime = !showTime;
    var divArray = document.getElementsByClassName("t");
    if (showTime) {
        document.getElementById("showtime").innerHTML = "Скрыть время в таблице";
        document.cookie = "showTime=1;";
        for (i = 0; i < divArray.length; i++)
            divArray[i].style.display = "block";
    } else {
        document.getElementById("showtime").innerHTML = "Показать время в таблице";
        document.cookie = "showTime=0;";
        for (i = 0; i < divArray.length; i++)
            divArray[i].style.display = "none";
    }
}

function getGradientColor(value, start, finish) {
    var result = "", a, b, s;
    a = start >> 16;
    b = finish >> 16;
    s = parseInt(value * (b - a) + a).toString(16);
    if (s.length == 1)
        s = '0' + s;
    result += s;
    a = (start >> 8) & 0xFF;
    b = (finish >> 8) & 0xFF;
    s = parseInt(value * (b - a) + a).toString(16);
    if (s.length == 1)
        s = '0' + s;
    result += s;
    a = start & 0xFF;
    b = finish & 0xFF;
    s = parseInt(value * (b - a) + a).toString(16);
    if (s.length == 1)
        s = '0' + s;
    return result + s;
}

function compareArrays(a, b) {
    //null больше любого массива.
    if (a == null)
        return 1;
    if (b == null)
        return -1;
    for (var i = 0, len = a.length; i < len; i++) {
        var x = +a[i], y = +b[i];
        if (x < y)
            return -1;
        if (x > y)
            return 1;
    }
    return 0;
}

function internalInit() {
    var i, j;

    var showtimeButton = document.getElementById("showtime");
    if (showtimeButton) {
        showtimeButton.addEventListener("click", changeShowTimeState);
        if (~document.cookie.indexOf("showTime=0"))
            changeShowTimeState();
    }

    var table = document.getElementsByClassName("standings-table")[0];
    table.style.width = "100%";

    var rows = table.rows;
    var rowCount = rows.length;
    if (rowCount == 1)
        return;
    var colCount = rows[0].childElementCount;

    var colStart = 1, colFin = 0;
    var firstRowCells = rows[0].children;
    for (i = 0; i < colCount; i++) {
        var firstRowCell = firstRowCells[i].firstChild.data.trim();
        if (firstRowCell == "A")
            colStart = i;
        if (firstRowCell.length == 1)
            colFin = i;
    }

    var rowStart = 1, rowFin = rowCount - 1;
    for (i = 1; i < rowCount; i++) {
        if (rows[i].children[0].firstChild == null) {
            rowFin = i - 1;
            break;
        }
    }

    var firstAccepted = new Array(colCount - 2);
    for (i = 0, len = firstAccepted.length; i < len; i++)
        firstAccepted[i] = [null, [ ]]
    for (i = rowStart; i <= rowFin; i++) {
        var cells = rows[i].children;
        for (j = colStart; j <= colFin; j++) {
            var s = cells[j].firstChild.data;
            var ac = s[0] == '+';
            var has_time = cells[j].firstChild != cells[j].lastChild;

            if (ac)
                cells[j].className = "g";
            else if (s[0] == '‒')
                cells[j].className = "r";
            else if (s[0] != '.') {
                var x = parseFloat(s) * .01;
                ac = x > .99999;
                cells[j].style.backgroundColor = '#' + getGradientColor(x, 0xEBAFA1, 0xAAD7A0);
            }

            if (ac && has_time) {
                var arr = cells[j].lastChild.data.split(':');
                var sign = compareArrays(arr, firstAccepted[j - 2][0]);
                if (sign < 0)
                    firstAccepted[j - 2] = [arr, [cells[j]]];
                else if (!sign)
                    firstAccepted[j - 2][1].push(cells[j]);
            }

            if (has_time) {
                var timeElement = cells[j].lastChild;

				var timeDiv = document.createElement("div");
				timeDiv.className = "t";
				var textNode = document.createTextNode(timeElement.data);
				timeDiv.appendChild(textNode);

				timeElement.data = "";
				cells[j].appendChild(timeDiv);
            }
        }
    }
    var fALen = firstAccepted.length;
    for (i = 0; i < fALen; i++) {
        var fALen2 = firstAccepted[i][1].length;
        for (j = 0; j < fALen2; j++) {
            firstAccepted[i][1][j].style.color = "";
            firstAccepted[i][1][j].className = "g fa";
        }
    }

	var element = document.createElement('style'), sheet;
	// Append style element to head
	document.head.appendChild(element);
	// Reference to the stylesheet
	sheet = element.sheet;
	sheet.insertRule(".g { background-color: #AAD7A0; }", 0);
	sheet.insertRule(".r { background-color: #EBAFA1; }", 1);
	sheet.insertRule(".fa { background-color: #67D367; }", 2);
}

window.addEventListener("DOMContentLoaded", internalInit, false);