module.exports = {
    configureWebpack: {
        devServer: {
            proxy: {
                '/state|/job|/run': {
                    target: 'http://localhost:8081/',
                }
            }
        }
    }
};
