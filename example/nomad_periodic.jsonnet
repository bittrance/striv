{
  Type: 'batch',
  Name: 'periodic',
  Datacenters: ['dc1'],
  Periodic: {
    Spec: "*/5 * * * * *",
  },
  TaskGroups: [
    {
      Count: 1,
      Name: 'group1',
      Tasks: [
        {
          Config: {
            image: 'alpine:latest',
            command: '/bin/sh',
            args: ['-c', params.command],
          },
          Driver: 'docker',
          Name: 'task1',
          Resources: {
            CPU: 500,
            MemoryMB: 256
          }
        }
      ]
    }
  ],
}
