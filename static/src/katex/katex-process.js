(function(){
    var e = document.getElementsByClassName("math");
    for (var i = 0, n = e.length; i < n; i++)
        katex.render(e[i].firstChild.data, e[i]);
})();
