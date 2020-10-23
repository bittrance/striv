{
  Name: 'example',
  Datacenters: ['dc1'],
  TaskGroups: [
    {
      Count: 1,
      Name: 'testi',
      Tasks: [
        {
          Config: {
            image: 'alpine:latest',
            command: '/bin/sh',
            args: ['-c', 'echo "' + params.greeting + '"'],
          },
          Driver: 'docker',
          Name: 'testo',
          Resources: {
            CPU: 500,
            MemoryMB: 256
          }
        }
      ]
    }
  ],
  Type: 'batch'
}
 