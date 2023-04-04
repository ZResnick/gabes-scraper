import React, {useState} from 'react';

export default function FormArea(props) {
    const [email, setEmail] = useState([null])
    const [password, setPassword] = useState([null])
    const [rootUrl, setRootUrl] = useState([null])

    return (
        <div>
            <nav className="navbar navbar-dark bg-dark">
                <div className="row col-12 d-flex justify-content-center text-white">
                    <span className="h3">input parameters</span>
                </div>
            </nav>
            <div className="wrapper">
                <form width="500px">
                    <div className="form-group">
                        <label htmlFor="rootUrl">Root URL </label>
                        <input type="url" className="form-control" id="rootUrl"
                               placeholder="Enter root URL" onChange={e => setRootUrl(e.target.value)} />
                        <small id="emailHelp" className="form-text text-muted">
                            please provide the top-level <b>album</b> that contains all sub-albums and photos</small>
                    </div>
                    <div className="form-group">
                        <label htmlFor="email">Email address </label>
                        <input type="email" className="form-control" id="email"
                               placeholder="Enter email (optional)" onChange={e => setEmail(e.target.value)} />
                        <small id="emailHelp" className="form-text text-muted">optional - some pages only require a password</small>
                    </div>
                    <div className="form-group">
                        <label htmlFor="exampleInputPassword1">Password</label>
                        <input type="password" className="form-control" id="exampleInputPassword1" placeholder="Password"
                               onChange={e => setPassword(e.target.value)} />
                    </div>

                    <button type="submit" className="btn btn-primary" onClick={(event) => {
                        event.preventDefault();

                        console.log("BUTTON HAS BEEN CLICKED")
                        const url = "http://localhost:5111/download"
                        let params = {
                            password: password,
                            root_url: rootUrl,
                        }
                        if (email) {
                            params.email = email;
                        }
                        console.log(params)

                        fetch(url, {
                            method: 'POST',
                            body: JSON.stringify(params),
                        })
                            .then(res => {
                                return res.json();
                            }, err => {
                                console.log(err)
                            })

                    }}>Begin download</button>
                </form>
            </div>
        </div>
    )
}