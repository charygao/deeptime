import numpy as np
import pytest
from numpy.testing import *

from sktime.numeric import is_diagonal_matrix, mdot, spd_eig, spd_inv, ZeroRankError, spd_inv_sqrt, spd_inv_split, \
    eig_corr


def test_is_diagonal_matrix():
    assert_(is_diagonal_matrix(np.diag([1, 2, 3, 4, 5])))
    assert_(not is_diagonal_matrix(np.array([[1, 2], [3, 4]])))


def test_mdot():
    A = np.random.normal(size=(5, 10))
    B = np.random.normal(size=(10, 20))
    C = np.random.normal(size=(20, 30))
    assert_almost_equal(mdot(A, B, C), A @ B @ C)


@pytest.fixture
def spd_matrix():
    X = np.random.normal(size=(50, 3))
    mat = X @ X.T  # positive semi-definite with rank 3
    return mat


@pytest.mark.parametrize('epsilon', [1e-5, 1e-12], ids=lambda x: f"epsilon={x}")
@pytest.mark.parametrize('method', ['QR', 'schur'], ids=lambda x: f"method={x}")
@pytest.mark.parametrize('canonical_signs', [False, True], ids=lambda x: f"canonical_signs={x}")
def test_spd_eig(spd_matrix, epsilon, method, canonical_signs):
    sm, vm = spd_eig(spd_matrix, epsilon=epsilon, method=method, canonical_signs=canonical_signs)
    assert_(sm[0] >= sm[1] >= sm[2])
    assert_array_almost_equal(vm @ np.diag(sm) @ vm.T, spd_matrix)
    assert_array_almost_equal(vm.T @ vm, np.eye(3))
    if canonical_signs or True:
        # largest element in each column in vm should be positive
        for col in range(vm.shape[1]):
            assert_(np.max(vm[:, col]) > 0)


@pytest.mark.parametrize('epsilon', [1e-5, 1e-12], ids=lambda x: f"epsilon={x}")
@pytest.mark.parametrize('method', ['QR', 'schur'], ids=lambda x: f"method={x}")
def test_spd_inv(spd_matrix, epsilon, method):
    W = spd_inv(spd_matrix, epsilon=epsilon, method=method)
    sm, _ = spd_eig(spd_matrix)
    sminv, _ = spd_eig(W)
    assert_array_almost_equal(np.sort(sm), np.sort(1. / sminv))


def test_spd_inv_1d():
    with assert_raises(ZeroRankError):
        spd_inv(np.array([[1e-18]]), epsilon=1e-10)  # smaller than epsilon

    assert_almost_equal(spd_inv(np.array([[5]])), 1 / 5)


@pytest.mark.parametrize('epsilon', [1e-5, 1e-12], ids=lambda x: f"epsilon={x}")
@pytest.mark.parametrize('method', ['QR', 'schur'], ids=lambda x: f"method={x}")
@pytest.mark.parametrize('return_rank', [True, False], ids=lambda x: f"return_rank={x}")
def test_spd_inv_split(spd_matrix, epsilon, method, return_rank):
    M = spd_inv_sqrt(spd_matrix, epsilon=epsilon, method=method, return_rank=return_rank)
    if return_rank:
        rank = M[1]
        M = M[0]

        assert_equal(rank, 3)

    assert_array_almost_equal(M @ M.T, spd_inv(spd_matrix))


@pytest.mark.parametrize('epsilon', [1e-5, 1e-12], ids=lambda x: f"epsilon={x}")
@pytest.mark.parametrize('method', ['QR', 'schur'], ids=lambda x: f"method={x}")
@pytest.mark.parametrize('canonical_signs', [False, True], ids=lambda x: f"canonical_signs={x}")
def test_spd_inv_split(spd_matrix, epsilon, method, canonical_signs):
    split = spd_inv_split(spd_matrix, epsilon=epsilon, method=method, canonical_signs=canonical_signs)
    spd_matrix_inv = split @ split.T
    sminv, _ = spd_eig(spd_matrix_inv)
    sm, _ = spd_eig(spd_matrix)
    assert_array_almost_equal(np.sort(sm), np.sort(1. / sminv)[-3:])
    if canonical_signs:
        for i in range(3):
            assert_(np.max(split[:, i]) > 0)


def test_spd_inv_split_nocutoff():
    x = np.random.normal(size=(5, 5))
    unitary = np.linalg.qr(x)[0]
    assert_array_almost_equal(unitary @ unitary.T, np.eye(5))
    spd = unitary @ np.diag([1., 2., 3., 4., 5.]) @ unitary.T
    w, _ = np.linalg.eigh(spd)
    L = spd_inv_split(spd, epsilon=0)
    spd_inv = L @ L.T
    assert_array_almost_equal(spd_inv, np.linalg.pinv(spd))


@pytest.mark.parametrize('epsilon', [1e-5, 1e-12], ids=lambda x: f"epsilon={x}")
@pytest.mark.parametrize('method', ['QR', 'schur'], ids=lambda x: f"method={x}")
@pytest.mark.parametrize('canonical_signs', [False, True], ids=lambda x: f"canonical_signs={x}")
@pytest.mark.parametrize('return_rank', [True, False], ids=lambda x: f"return_rank={x}")
def test_eig_corr(epsilon, method, canonical_signs, return_rank):
    data = np.random.normal(size=(5000, 3))
    from sktime.covariance import Covariance
    covariances = Covariance(lagtime=10, compute_c00=True, compute_ctt=True).fit(data).fetch_model()
    out = eig_corr(covariances.cov_00, covariances.cov_tt, epsilon=epsilon, method=method,
                   canonical_signs=canonical_signs, return_rank=return_rank)
    eigenvalues = out[0]
    eigenvectors = out[1]
    if return_rank:
        rank = out[2]
        assert_equal(rank, len(eigenvalues))

    for r in range(len(out[0])):
        np.testing.assert_array_almost_equal(covariances.cov_00 @ eigenvectors[r] * eigenvalues[r],
                                             covariances.cov_tt @ eigenvectors[r], decimal=2)