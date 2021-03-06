import React, { useEffect } from 'react'
import { connect } from 'react-redux'

import * as actions from '../../../store/actions'

const Logout = React.memo(props => {

    useEffect(() => {
        props.userDetailsReset()
        const timer = setTimeout(() => props.logoutHandler(), 500)

        return () => {
            clearTimeout(timer)
        }
    }, [props])



    return (
        <div style={{ margin: '10px auto', textAlign: 'center', fontWeight: 'bold' }}>
            Logging out.....
        </div>
    )
})

const mapStateToProps = (state) => ({

})

const mapDispatchToProps = dispatch => {
    return {
        logoutHandler: () => dispatch(actions.authLogout()),
        userDetailsReset: () => dispatch(actions.userDetailsReset()),

    }
}

export default connect(mapStateToProps, mapDispatchToProps)(Logout)
