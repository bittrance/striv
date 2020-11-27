module.exports = {
    configureWebpack: {
        devServer: {
            proxy: {
                '/job|/public-key|/run|/state': {
                    target: 'http://localhost:8081/',
                }
            }
        }
    }
};
