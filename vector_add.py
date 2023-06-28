import torch
import triton
import triton.language as tl

@triton.jit
def add_kernel(
    x_ptr,
    y_ptr,
    output_ptr,
    n_elements,
    BLOCK_SIZE: tl.constexpr,
):
    pid = tl.program_id(axis=0)

    block_start = pid * BLOCK_SIZE
    offsets = block_start + tl.arange(0, BLOCK_SIZE)

    mask = offsets < n_elements
    x = tl.load(x_ptr + offsets, mask = mask)
    y = tl.load(y_ptr + offsets, mask = mask)

    output = x + y
    tl.store(output_ptr + offsets, output, mask = mask)


def add(x: torch.Tensor, y: torch.Tensor):
    output = torch.empty_like(x)
    assert x.is_cuda and y.is_cuda and output.is_cuda

    n_elements = output.numel()

    grid = lambda meta: (triton.cdiv(n_elements, meta['BLOCK_SIZE']), )

    add_kernel[grid](x, y, output, n_elements, BLOCK_SIZE=1024)

    return output

def test():
    torch.manual_seed(0)
    size = 98432

    x = torch.rand(size, device='cuda')
    y = torch.rand(size, device="cuda")

    output_torch = x + y
    output_triton = add(x, y)
    print(
        f'The maximum difference between torch and triton is '
        f'{torch.max(torch.abs(output_torch - output_triton))}'
    )


if __name__ == "__main__":
    test()