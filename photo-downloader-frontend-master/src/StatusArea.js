import React from 'react';


// todo: create pinging function to get status
// todo: on server side, add second thread to allow for status in parallel
// todo: check server for whether busy, if busy don't start another job
// todo: provide updates using: # of urls written to download file
// todo: provide updates using: # of files at leaf level (downloaded)

const status_route = 'http://localhost:5000/status'


class StatusArea extends React.Component {
    constructor(props) {
        super(props);

        // Set defaults
        this.state = {
            timeElapsed: -1,
            currentTask: 'idle',
            currentTaskDesc: null,
            logOutProgress: []
        }

        this.componentWillUnmount = this.componentWillUnmount.bind(this);
        this.componentDidMount = this.componentDidMount.bind(this);
        this.getDesc = this.getDesc.bind(this);
        this.getTime = this.getTime.bind(this);
        this.tick = this.tick.bind(this);
    }

    /**
     * Setup the tick interval
     */
    componentDidMount() {
        this.intervalID = setInterval(
            () => this.tick(),
            5000
        );
    }

    /**
     * Clock ticking
     */
    tick() {
        console.log("Fetching")
        fetch(status_route, {method: 'GET'}).then(
            res => {
                return res.json();
            }, err => {
                console.log(err);
            }).then(data => {
                console.log("Got back this data")
                console.log(JSON.stringify(data))
                if (!data) return;
                // timeElapsed
                this.setState({
                    timeElapsed: data.time_elapsed,
                    currentTask: data.current_task,
                    currentTaskDesc: data.current_task_desc,
                    logOutProgress: data.log_progress,
                })
            }
        )
    }

    /**
     * Clear out the intervalID for reset
     */
    componentWillUnmount() {
        clearInterval(this.intervalID);
    }

    /**
     * Get the current description, if not null
     */
    getDesc() {
        if (this.state.currentTaskDesc) {
            return (
                <i>
                    {this.state.currentTaskDesc}
                    <br /> <br />
                </i>
            )
        }
    }

    getLogProgress() {
        if (this.state.logOutProgress) {
            return (
              <i><ul>
                  {this.state.logOutProgress.map(i => {
                      return <li>{i}</li>
                  })}
                  <br /> <br />
              </ul></i>
            )
        }
    }

    /**
     * Get the current elapsed time, if not null
     */
    getTime() {
        if (this.state.currentTaskDesc) {
            return (
                <div>
                    <label>Time Elapsed:</label>
                    {this.state.timeElapsed}
                </div>
            )
        }
    }

    render() {
        return (
            <>{/*Status area*/}
                <nav className="navbar navbar-dark bg-dark">
                    <div className="row col-12 d-flex justify-content-center text-white">
                        <span className="h4">process status</span>
                    </div>
                </nav>
                <div className="wrapper-wide">
                    <label>Current Task:</label> {this.state.currentTask} <br />
                    {this.getDesc()}
                    {this.getTime()}
                    {this.getLogProgress()}
                </div>
            </>

        )
    }
}

export default StatusArea;