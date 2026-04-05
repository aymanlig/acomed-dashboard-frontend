import React, { useState } from 'react'; // 1. ضروري نعيطو لـ useState
import './LoginPage.css'; 

const LoginPage = () => {

    // 2. هادو هما الذاكرات (States) اللي غنخبيو فيهم المعلومات
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [buttonText, setButtonText] = useState('Sign In'); // السمية الأصلية د البوطونة

    // هاد الفانكشن كيتعيط ليها ملي كنكليكيو على البوطونة
    const handleLogin = (e) => {
        e.preventDefault(); // باش الصفحة ماديرش ريفريش

        // 3. هاهي الـ if العادية اللي هضرتي عليها
        if (email === '17ay2004@gmail.com' && password === '12345678') {
            setButtonText('كاين راه تسجلتي'); // يلا كان صحيح، بدلو السمية د البوطونة
            console.log("راك دخلتي بنجاح!");
        } else {
            setButtonText('غلط، عاود جرب'); // نقدر نزيدو هادي يلا كتب شي حاجة غالطة
            console.log("الإيميل ولا المودباس غالطين");
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <h2>LOGIN</h2>

                <form onSubmit={handleLogin}>
                    <div className="input-group">
                        <input
                            type="text"
                            placeholder="l"
                            required
                            value={email} // ربطنا الخانة بالذاكرة ديال الإيميل
                            onChange={(e) => setEmail(e.target.value)} // ملي يكتب، كنخبيو داكشي فـ email
                        />
                        <i className="fas fa-user"></i>
                    </div>

                    <div className="input-group">
                        <input
                            type="password"
                            placeholder="Password"
                            required
                            value={password} // ربطنا الخانة بالذاكرة ديال المودباس
                            onChange={(e) => setPassword(e.target.value)} // ملي يكتب، كنخبيو داكشي فـ password
                        />
                        <i className="fas fa-lock"></i>
                    </div>

                    <div className="options">
                        <label>
                            <input type="checkbox" /> Remember me
                        </label>
                        <a href="#">Forgot password?</a>
                    </div>

                    {/* هنا عيطنا للستيت ديال السمية د البوطونة باش تتبدل أوتوماتيكيا */}
                    <button type="submit" className="btn-login">{buttonText}</button>
                </form>

                <div className="divider">OR</div>

                <div className="social-login">
                    <a href="#"><i className="fab fa-google"></i></a>
                    <a href="#"><i className="fab fa-facebook-f"></i></a>
                    <a href="#"><i className="fab fa-twitter"></i></a>
                </div>

                <div className="register-link">
                    Don't have an account? <a href="#">Register</a>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;