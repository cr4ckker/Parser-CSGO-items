var form_login = document.getElementById("loginForm");
var form_reg   = document.getElementById("signupForm");

var btn_open_up = document.getElementById("signupOpen");
var btn_open_in = document.getElementById("signinOpen");

var btn_login = document.getElementById("login");
var btn_signup = document.getElementById("signup"); 

var errorText = document.getElementById("error_info");

btn_open_in.addEventListener("click", function () { Open_signin(); });
btn_open_up.addEventListener("click", function () { Open_signup(); });
btn_login.addEventListener("click", function () { Login(); });
btn_signup.addEventListener("click", function () { Signup(); });

function Open_signup()
{
    form_reg.setAttribute("style", "display: block;");
    form_login.setAttribute("style", "display: none;");
    errorText.textContent = '';
}

function Open_signin()
{
    form_reg.setAttribute("style", "display: none;");
    form_login.setAttribute("style", "display: block;");
    errorText.textContent = '';
}

function Login()
{   
    var login = document.getElementById('signin_login').value;
    var password = document.getElementById('signin_pass').value;
    var Request = new XMLHttpRequest();

    Request.responseType = 'json';
    Request.open("POST", "./auth?mode=login&login=" + login + "&password=" + password, true);
    Request.send();
    Request.onload = function() {
        let responseObj = Request.response;
        if(responseObj['success']){
            errorText.setAttribute('class', 'text-success lead')
            errorText.textContent = 'Авторизация пройдена! Переадресация...';
            location.href = './';
        }
        else{
            errorText.setAttribute('class', 'text-danger lead')
            errorText.textContent = 'Ошибка: ' + responseObj['error'];
        }
      }
}

function Signup()
{   
    var login = document.getElementById('signup_login').value;
    var password = document.getElementById('signup_pass').value;
    var rpassword = document.getElementById('signup_rpass').value;
    if(password == rpassword){
        var Request = new XMLHttpRequest();
        if(login.length > 2 & password.length > 6){
            Request.responseType = 'json';
            Request.open("POST", "./auth?mode=register&login=" + login + "&password=" + password, true);
            Request.send();
            Request.onload = function() {
                let responseObj = Request.response;
                if(responseObj['success']){
                    errorText.setAttribute('class', 'text-success lead')
                    errorText.textContent = 'Авторизация пройдена! Переадресация...';
                    location.href = './';
                }
                else{
                    errorText.setAttribute('class', 'text-danger lead')
                    errorText.textContent = 'Ошибка: ' + responseObj['error'];
                }
            }
        }
        else
        {
            errorText.setAttribute('class', 'text-danger lead')
            errorText.textContent = 'Ошибка: Мало символов в логине или в пароле';
        }
    }
    else
    {
    errorText.setAttribute('class', 'text-danger lead')
    errorText.textContent = 'Ошибка: Пароли не совпадают';
    };
}