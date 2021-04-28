var btn = document.getElementById("theme-button");
var link = document.getElementById("theme-link");
var logo = document.getElementById('logo');

btn.addEventListener("click", function () { ChangeTheme(); });

function ChangeTheme()
{
    let lightTheme = "static/light.css";
    let darkTheme = "static/dark.css";

    var currTheme = link.getAttribute("href");
    var logoTheme = "";
    var theme = "";

    if(currTheme == lightTheme)
    {
   	 currTheme = darkTheme;
     logoTheme = '/static/logo-dark.png';
   	 theme = "dark";
    }
    else
    {    
   	 currTheme = lightTheme;
     logoTheme = '/static/logo-light.png';
   	 theme = "light";
    }

    link.setAttribute("href", currTheme);
    logo.setAttribute("src", logoTheme);

    Save(theme);
}

function Save(theme)
{
    var Request = new XMLHttpRequest();
    Request.open("POST", "./ThemeSave?theme=" + theme, true);
    Request.send();
}